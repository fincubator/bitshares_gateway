from decimal import Decimal
from uuid import UUID, uuid4
import asyncio

import psycopg2
import sqlalchemy as sa

from booker.app import AppContext
from booker.gateway.dto import OrderType, ValidateAddress, GetDepositAddress
from booker.frontend.dto import NewInOrder, InOrder, Order
from booker.db.models import Tx as TxModel, Order as OrderModel


async def new_in_order(context: AppContext, args: NewInOrder) -> InOrder:
    assert (
        args.in_tx_coin == "USDT"
        and args.out_tx_coin == "FINTEH.USDT"
        or args.in_tx_coin == "FINTEH.USDT"
        and args.out_tx_coin == "USDT"
    )
    assert args.in_tx_amount >= Decimal("0.0")

    if args.out_tx_to is not None:
        validate_address_args = ValidateAddress(tx_to=args.out_tx_to)
        out_gateway = context.gateway_clients[args.out_tx_coin]
        out_gateway_coro = out_gateway.validate_address(validate_address_args)

        while True:
            try:
                validated_address = await out_gateway_coro.asend(None)
            except StopAsyncIteration:
                break

        assert validated_address.valid == True

    get_deposit_address_args = GetDepositAddress(out_tx_to=args.out_tx_to)
    in_gateway = context.gateway_clients[args.in_tx_coin]
    in_gateway_coro = in_gateway.get_deposit_address(get_deposit_address_args)

    while True:
        try:
            deposit_address = await in_gateway_coro.asend(None)
        except StopAsyncIteration:
            break

    if args.in_tx_coin == "USDT" and args.out_tx_coin == "FINTEH.USDT":
        order_type = OrderType.DEPOSIT
    elif args.in_tx_coin == "FINTEH.USDT" and args.out_tx_coin == "USDT":
        order_type = OrderType.WITHDRAWAL

    in_tx_id = uuid4()
    in_tx_query = sa.insert(TxModel).values(
        id=in_tx_id,
        coin=args.in_tx_coin,
        to_address=deposit_address.tx_to,
        amount=args.in_tx_amount,
    )
    out_tx_id = uuid4()
    out_tx_query = sa.insert(TxModel).values(id=out_tx_id, coin=args.out_tx_coin,)
    order_id = uuid4()
    order_query = sa.insert(OrderModel).values(
        id=order_id, type=order_type, in_tx=in_tx_id, out_tx=out_tx_id,
    )

    async with context.db_engine.acquire() as connection:
        while True:
            try:
                async with connection.begin("SERIALIZABLE") as transaction:
                    await connection.execute(in_tx_query)
                    await connection.execute(out_tx_query)
                    await connection.execute(order_query)

                break
            except psycopg2.errors.SerializationFailure:
                continue

    order = InOrder(order_id=order_id, in_tx_to=deposit_address.tx_to)

    return order


async def get_order(context: AppContext, order_id: UUID) -> Order:
    OutTxModel = sa.alias(TxModel)
    where = (
        (OrderModel.id == order_id)
        & (Order.in_tx == TxModel.id)
        & (Order.out_tx == OutTxModel.c.id)
    )
