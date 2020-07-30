from typing import AsyncGenerator
from decimal import Decimal
from uuid import uuid4
import asyncio
import logging

import psycopg2
import sqlalchemy as sa

from booker.app import AppContext
from booker.gateway.dto import (
    OrderType,
    TxError,
    NewInOrder,
    NewOutOrder,
    NewInOrderRequest,
    NewInTxOrder,
    NewOutTxOrder,
    UpdateTxOrder,
)
from booker.db.models import GatewayParty, Tx, Order


async def new_in_order(context: AppContext, args: NewInOrder) -> None:
    assert args.order_type != OrderType.TRASH
    assert args.in_tx_amount >= Decimal("0.0")
    assert args.in_tx_created_at >= 0
    assert args.in_tx_error == TxError.NO_ERROR
    assert args.in_tx_confirmations >= 0
    assert args.in_tx_confirmations >= args.in_tx_max_confirmations

    in_gateway = context.gateway_clients[order.in_tx_coin]
    in_gateway_coro = out_gateway.new_in_order(in_order)

    while True:
        try:
            await in_gateway_coro.send(None)
        except StopAsyncIteration:
            break

    InTx = sa.alias(Tx)
    where = (
        (Order.id == args.order_id)
        & (Order.type == args.order_type)
        & (Order.party == GatewayParty.INIT)
        & (Order.in_tx == Tx.id)
        & (Tx.tx_id == None)
        & (Tx.from_address == None)
        & (Tx.to_address == args.in_tx_to)
        & (Tx.amount == args.in_tx_amount)
        & (Tx.error == TxError.NO_ERROR)
        & (Tx.confirmations == 0)
        & (Tx.confirmations == Tx.max_confirmations)
        & (Order.out_tx == OutTx.c.id)
        & (OutTx.c.tx_id == None)
        & (OutTx.c.from_address == None)
        & (OutTx.c.to_address == args.out_tx_from)
        & (OutTx.c.amount == Decimal("0.0"))
        & (OutTx.c.error == TxError.NO_ERROR)
        & (OutTx.c.confirmations == 0)
        & (OutTx.c.confirmations == OutTx.c.max_confirmations)
    )
    query = (
        sa.update(Order)
        .where(where)
        .values(party=GatewayParty.IN_CREATED)
        .returning(Order.id)
    )

    async with context.db_engine.acquire() as connection:
        while True:
            try:
                async with connection.begin("SERIALIZABLE") as transaction:
                    result = await connection.execute(query)

                    assert result.rowcount == 1

                break
            except psycopg2.errors.SerializationFailure:
                continue


async def new_out_order(context: AppContext, args: NewOutOrder) -> None:
    assert args.order_type != OrderType.TRASH
    assert args.in_tx_amount > Decimal("0.0")
    assert args.in_tx_created_at >= 0
    assert args.in_tx_error == TxError.NO_ERROR
    assert args.in_tx_confirmations >= 0
    assert args.in_tx_confirmations >= args.in_tx_max_confirmations

    out_gateway = context.gateway_clients[order.out_tx_coin]
    out_gateway_coro = out_gateway.new_out_order(args)

    while True:
        try:
            await out_gateway_coro.send(None)
        except StopAsyncIteration:
            break

    InTx = sa.alias(Tx)
    where = (
        (Order.id == args.order_id)
        & (Order.type == args.order_type)
        & (Order.party == GatewayParty.IN_CREATED)
        & (Order.in_tx == InTx.c.id)
        & (InTx.c.coin == args.in_tx_coin)
        & (InTx.c.tx_id == args.in_tx_hash)
        & (InTx.c.from_address == args.in_tx_from)
        & (InTx.c.to_address == args.in_tx_to)
        & (InTx.c.amount == args.in_tx_amount)
        & (InTx.c.created_at == args.in_tx_created_at)
        & (InTx.c.error == args.in_tx_error)
        & (InTx.c.confirmations == args.in_tx_confirmations)
        & (InTx.c.max_confirmations == args.in_tx_max_confirmations)
        & (Order.out_tx == Tx.id)
        & (Tx.coin == args.out_tx_coin)
        & (Tx.to_address == args.out_tx_to)
    )
    query = (
        sa.update(Order)
        .where(where)
        .values(party=GatewayParty.OUT_CREATED)
        .returning(Order.id)
    )

    async with context.db_engine.acquire() as connection:
        while True:
            try:
                async with connection.begin("SERIALIZABLE") as transaction:
                    result = await connection.execute(query)

                    assert result.rowcount == 1

                break
            except psycopg2.errors.SerializationFailure:
                continue


async def new_in_order_request(context: AppContext, args: NewInOrderRequest) -> None:
    assert args.order_type != OrderType.TRASH
    assert args.in_tx_amount > Decimal("0.0")

    in_tx_id = uuid4()
    in_tx_query = sa.insert(Tx).values(
        id=in_tx_id,
        coin=args.in_tx_coin,
        to_address=args.in_tx_to,
        amount=args.in_tx_amount,
    )
    out_tx_id = uuid4()
    out_tx_query = sa.insert(Tx).values(id=out_tx_id, coin=args.out_tx_coin)
    order_id = uuid4()
    order_query = sa.insert(Tx).values(
        type=args.order_type, in_tx=in_tx_id, out_tx=out_tx_id
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


async def new_in_tx_order(context: AppContext, args: NewInTxOrder) -> None:
    assert args.tx_amount > Decimal("0.0")
    assert args.tx_created_at >= 0
    assert args.tx_confirmations >= 0
    assert args.tx_max_confirmations >= 0

    OutTx = sa.alias(Tx)
    update_in_tx_where = (
        (Order.id == args.order_id)
        & (Order.type != OrderType.TRASH)
        & (Order.party == GatewayParty.IN_CREATED)
        & (Order.in_tx == Tx.id)
        & (Tx.to_address != None)
        & (
            (Tx.tx_id == None)
            & (Tx.from_address == None)
            & (Tx.amount >= Decimal("0.0"))
            & (Tx.error == TxError.NO_ERROR)
            & (Tx.confirmations == 0)
            & (Tx.max_confirmations == 0)
            | (Tx.tx_id == args.tx_hash)
            & (Tx.from_address == args.tx_from)
            & (Tx.amount == args.tx_amount)
            & (Tx.created_at == args.tx_created_at)
            & (Tx.error == args.tx_error)
            & (Tx.confirmations == args.tx_confirmations)
            & (Tx.max_confirmations == args.tx_max_confirmations)
        )
        & (Order.out_tx == OutTx.c.id)
        & (OutTx.c.tx_id == None)
        & (OutTx.c.from_address == None)
        & ((OutTx.c.to_address == None) | (OutTx.c.to_address == args.memo_to))
        & (OutTx.c.error == TxError.NO_ERROR)
        & (OutTx.c.confirmations == 0)
        & (OutTx.c.max_confirmations == 0)
    )
    update_in_tx_query = (
        sa.update(Tx)
        .values(
            tx_id=args.tx_hash,
            from_address=args.tx_from,
            amount=args.tx_amount,
            created_at=args.tx_created_at,
            error=args.tx_error,
            confirmations=args.tx_confirmations,
            max_confirmations=args.tx_max_confirmations,
        )
        .where(update_in_tx_where)
        .returning(Order.id)
    )
    update_out_tx_where = (Order.id == args.order_id) & (Order.out_tx == Tx.id)
    update_out_tx_query = (
        sa.update(Tx).values(to_address=args.memo_to).where(update_out_tx_where)
    )

    async with context.db_engine.acquire() as connection:
        while True:
            try:
                async with connection.begin("SERIALIZABLE") as transaction:
                    result = await connection.execute(update_in_tx_query)

                    assert result.rowcount == 1

                    await connection.execute(update_out_tx_query)

                break
            except psycopg2.errors.SerializationFailure:
                continue

    if args.confirmations < args.max_confirmations:
        return

    out_order = NewOutOrder(
        order_id=args.order_id,
        order_type=order.type,
        in_tx_coin=order.in_tx_coin,
        in_tx_hash=args.tx_hash,
        in_tx_from=args.tx_from,
        in_tx_to=order.in_tx_to_address,
        in_tx_amount=args.tx_amount,
        in_tx_created_at=args.tx_created_at,
        in_tx_error=args.tx_error,
        in_tx_confirmations=args.tx_confirmations,
        in_tx_max_confirmations=args.tx_max_confirmations,
        out_tx_coin=out_order.out_tx_coin,
        out_tx_to=out_order.out_tx_to_address,
    )

    await new_out_order(out_order)


async def update_in_tx_order(context: AppContext, args: UpdateTxOrder) -> None:
    assert args.tx_confirmations >= 0
    assert args.tx_max_confirmations >= 0

    OutTx = sa.alias(Tx)
    where = (
        (Order.id == args.order_id)
        & (Order.type != OrderType.TRASH)
        & (Order.party == GatewayParty.IN_CREATED)
        & (Order.in_tx == Tx.id)
        & (Tx.tx_id != None)
        & (Tx.from_address != None)
        & (Tx.to_address != None)
        & (Tx.amount > Decimal("0.0"))
        & (Tx.error == TxError.NO_ERROR)
        & (Tx.confirmations >= 0)
        & (Tx.confirmations < Tx.max_confirmations)
        & (Order.out_tx == OutTx.c.id)
        & (OutTx.c.tx_id == None)
        & (OutTx.c.from_address == None)
        & (OutTx.c.to_address != None)
        & (OutTx.amount == Decimal("0.0"))
        & (OutTx.c.error == TxError.NO_ERROR)
        & (OutTx.c.confirmations == 0)
        & (OutTx.c.max_confirmations == 0)
    )
    query = (
        sa.update(Tx)
        .where(where)
        .values(
            error=args.tx_error,
            confirmations=args.tx_confirmations,
            max_confirmations=args.tx_max_confirmations,
        )
        .returning(Order.id)
    )

    async with context.db_engine.acquire() as connection:
        while True:
            try:
                async with connection.begin("SERIALIZABLE") as transaction:
                    result = await connection.execute(query)

                    assert result.rowcount == 1

                break
            except psycopg2.errors.SerializationFailure:
                continue


async def new_out_tx_order(context: AppContext, args: NewOutTxOrder) -> None:
    assert args.tx_amount > Decimal("0.0")
    assert args.tx_created_at >= 0
    assert args.tx_confirmations >= 0
    assert args.tx_max_confirmations >= 0

    InTx = sa.alias(Tx)
    where = (
        (Order.id == args.order_id)
        & (Order.type != OrderType.TRASH)
        & (Order.party == GatewayParty.OUT_CREATED)
        & (Order.in_tx == InTx.c.id)
        & (InTx.c.tx_id != None)
        & (InTx.c.from_address != None)
        & (InTx.c.to_address != None)
        & (InTx.c.amount > Decimal("0.0"))
        & (InTx.c.error == TxError.NO_ERROR)
        & (InTx.c.confirmations >= 0)
        & (InTx.c.confirmations < InTx.c.max_confirmations)
        & (Order.out_tx == Tx.id)
        & (Tx.to_address != None)
        & (
            (Tx.tx_id == None)
            & (Tx.from_address == None)
            & (Tx.status == TxStatus.WAIT)
            & (Tx.error == TxError.NO_ERROR)
            & (Tx.confirmations == 0)
            & (Tx.max_confirmations == 0)
            | (Tx.tx_id == args.tx_hash)
            & (Tx.from_address == args.tx_from)
            & (Tx.amount == args.tx_amount)
            & (Tx.created_at == args.tx_created_at)
            & (Tx.error == args.tx_error)
            & (Tx.confirmations == args.tx_confirmations)
            & (Tx.max_confirmations == args.tx_max_confirmations)
        )
    )
    query = (
        sa.update(Tx)
        .where(where)
        .values(
            tx_id=args.tx_hash,
            from_address=args.tx_from,
            amount=args.tx_amount,
            created_at=args.tx_created_at,
            error=args.tx_error,
            confirmations=args.tx_confirmations,
            max_confirmations=args.tx_max_confirmations,
        )
        .returning(Tx.id)
    )

    async with context.db_engine.acquire() as connection:
        while True:
            try:
                async with connection.begin("SERIALIZABLE") as transaction:
                    result = await connection.execute(query)

                    assert result.rowcount == 1

                break
            except psycopg2.errors.SerializationFailure:
                continue


async def update_out_tx_order(context: AppContext, args: UpdateTxOrder) -> None:
    assert args.tx_confirmations >= 0
    assert args.tx_max_confirmations >= 0

    InTx = sa.alias(Tx)
    where = (
        (Order.id == args.order_id)
        & (Order.type != OrderType.TRASH)
        & (Order.party == GatewayParty.OUT_CREATED)
        & (Order.in_tx == InTx.c.id)
        & (InTx.c.tx_id != None)
        & (InTx.c.from_address != None)
        & (InTx.c.to_address != None)
        & (InTx.c.amount > Decimal("0.0"))
        & (InTx.c.error == TxError.NO_ERROR)
        & (InTx.c.confirmations >= 0)
        & (InTx.c.confirmations < InTx.c.max_confirmations)
        & (Order.out_tx == Tx.id)
        & (Tx.tx_id != None)
        & (Tx.from_address != None)
        & (Tx.to_address != None)
        & (Tx.amount > Decimal("0.0"))
        & (Tx.confirmations >= 0)
        & (Tx.confirmations < Tx.max_confirmations)
    )
    query = (
        sa.update(Tx)
        .where(where)
        .values(
            error=args.tx_error,
            confirmations=args.tx_confirmations,
            max_confirmations=args.tx_max_confirmations,
        )
        .returning(Tx.id)
    )

    async with context.db_engine.acquire() as connection:
        while True:
            try:
                async with connection.begin("SERIALIZABLE") as transaction:
                    result = await connection.execute(query)

                    assert result.rowcount == 1

                break
            except psycopg2.errors.SerializationFailure:
                continue


async def process_in_orders(context: AppContext) -> AsyncGenerator[None, None]:
    OutTx = sa.alias(Tx)
    where = (
        (Order.type != OrderType.TRASH)
        & (Order.party == GatewayParty.INIT)
        & (Order.in_tx == Tx.id)
        & (Tx.tx_id == None)
        & (Tx.from_address == None)
        & (Tx.to_address != None)
        & (Tx.amount >= Decimal("0.0"))
        & (Tx.error == TxError.NO_ERROR)
        & (Tx.confirmations == 0)
        & (Tx.confirmations == Tx.max_confirmations)
        & (Order.out_tx == OutTx.c.id)
        & (OutTx.c.tx_id == None)
        & (OutTx.c.from_address == None)
        & (OutTx.c.amount == Decimal("0.0"))
        & (OutTx.c.error == TxError.NO_ERROR)
        & (OutTx.c.confirmations == 0)
        & (OutTx.c.confirmations == OutTx.c.max_confirmations)
    )
    query = (
        sa.select(
            [
                Order.id,
                Order.type,
                Tx.id.label("in_tx_id"),
                Tx.coin.label("in_tx_coin"),
                Tx.to_address.label("in_tx_to_address"),
                Tx.amount.label("in_tx_amount"),
                OutTx.c.id.label("out_tx_id"),
                OutTx.c.coin.label("out_tx_coin"),
                OutTx.c.to_address.label("out_tx_to_address"),
            ]
        )
        .where(where)
        .limit(1)
    )

    while True:
        async with context.db_engine.acquire() as connection:
            while True:
                try:
                    async with connection.begin("SERIALIZABLE", True) as transaction:
                        result = await connection.execute(query)
                        order = await result.fetchone()

                    break
                except psycopg2.errors.SerializationFailure:
                    yield

                    continue

        if order == None:
            yield

            continue

        in_order = NewInOrder(
            order_id=order.id,
            order_type=order.type,
            in_tx_coin=order.in_tx_coin,
            in_tx_to=order.in_tx_to_address,
            in_tx_amount=order.in_tx_amount,
            out_tx_coin=order.out_tx_coin,
            out_tx_to=order.out_tx_to_address,
        )

        await new_in_order(in_order)

        yield


async def process_out_orders(context: AppContext) -> AsyncGenerator[None, None]:
    InTx = sa.alias(Tx)
    where = (
        (Order.type != OrderType.TRASH)
        & (Order.party == GatewayParty.IN_CREATED)
        & (Order.in_tx == InTx.c.id)
        & (InTx.c.tx_id != None)
        & (InTx.c.from_address != None)
        & (InTx.c.to_address != None)
        & (InTx.c.amount > Decimal("0.0"))
        & (InTx.c.error == TxError.NO_ERROR)
        & (InTx.c.confirmations >= 0)
        & (InTx.c.confirmations >= InTx.c.max_confirmations)
        & (Order.out_tx == Tx.id)
        & (Tx.tx_id == None)
        & (Tx.from_address == None)
        & (Tx.to_address != None)
        & (Tx.amount == Decimal("0.0"))
        & (Tx.error == TxError.NO_ERROR)
        & (Tx.confirmations == 0)
        & (Tx.confirmations == Tx.max_confirmations)
    )
    query = (
        sa.select(
            [
                Order.id,
                Order.type,
                InTx.c.id.label("in_tx_id"),
                InTx.c.coin.label("in_tx_coin"),
                InTx.c.tx_id.label("in_tx_tx_id"),
                InTx.c.from_address.label("in_tx_from_address"),
                InTx.c.to_address.label("in_tx_to_address"),
                InTx.c.created_at.label("in_tx_created_at"),
                InTx.c.error.label("in_tx_error"),
                InTx.c.confirmations.label("in_tx_confirmations"),
                InTx.c.max_confirmations.label("in_tx_max_confirmations"),
                InTx.c.amount.label("in_tx_amount"),
                Tx.id.label("out_tx_id"),
                Tx.coin.label("out_tx_coin"),
                Tx.to_address.label("out_tx_to_address"),
            ]
        )
        .where(where)
        .limit(1)
    )

    while True:
        async with context.db_engine.acquire() as connection:
            while True:
                try:
                    async with connection.begin("SERIALIZABLE", True) as transaction:
                        result = await connection.execute(query)
                        order = await result.fetchone()

                    break
                except psycopg2.errors.SerializationFailure:
                    yield

                    continue

        if order == None:
            yield

            continue

        out_order = NewOutOrder(
            order_id=order.id,
            order_type=order.type,
            in_tx_coin=order.in_tx_coin,
            in_tx_hash=order.in_tx_tx_id,
            in_tx_from=order.in_tx_from_address,
            in_tx_to=order.in_tx_to_address,
            in_tx_amount=order.in_tx_amount,
            in_tx_created_at=order.in_tx_created_at,
            in_tx_error=order.in_tx_error,
            in_tx_confirmations=order.in_tx_confirmations,
            in_tx_max_confirmations=order.in_tx_max_confirmations,
            out_tx_coin=order.out_tx_coin,
            out_tx_to=order.out_tx_to_address,
        )

        await new_out_order(out_order)

        yield


async def process_orders(context: AppContext) -> None:
    logging.info("Orders server has started.")

    try:
        process_in_orders_coro = process_in_orders(context)
        process_out_orders_coro = process_out_orders(context)

        while True:
            try:
                await process_in_orders_coro.asend(None)
                await process_out_orders_coro.asend(None)
            except asyncio.CancelledError as exception:
                logging.debug("Orders server is stopping.")

                try:
                    await process_in_orders_coro.athrow(exception)
                except asyncio.CancelledError:
                    ...

                try:
                    await process_out_orders_coro.athrow(exception)
                except asyncio.CancelledError:
                    ...

                raise
    except asyncio.CancelledError:
        logging.info("Orders server has stopped.")

        raise
    except BaseException as exception:
        logging.exception(exception)

        raise exception
