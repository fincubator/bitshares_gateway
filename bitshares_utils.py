import asyncio
import logging

from bitshares.aio import BitShares
from bitshares.aio.account import Account
from bitshares.aio.asset import Asset
from bitshares.aio.amount import Amount
from bitshares.aio.blockchain import Block, Blockchain
from bitshares.aio.memo import Memo
from bitshares.aio.instance import (
    set_shared_bitshares_instance,
    shared_bitshares_instance,
)
from bitsharesbase.signedtransactions import Signed_Transaction
from graphenecommon.exceptions import BlockDoesNotExistsException

from dto import (
    OrderType,
    TxStatus,
    TxError,
    BitSharesOperation as BitSharesOperationDTO,
)
from config import BITSHARES_BLOCK_TIME, gateway_cfg


class InvalidMemoMask(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)


async def init_bitshares(
    account: str = None, node: str or list = None, keys: list = None, loop=None
) -> BitShares:
    """ Create bitshares aio.instance, append it to loop and set as shared """
    if not account:
        raise Exception(
            "You need to provide an gateway account. Gateway instance can not work without it!\n"
            "Check that your account is owner of asset that your instance will distribute!"
        )
    bitshares_instance = BitShares(node=node, keys=keys, loop=loop)
    set_shared_bitshares_instance(bitshares_instance)
    await bitshares_instance.connect()
    bitshares_instance.set_default_account(account)
    return bitshares_instance


async def broadcast_tx(tx: dict) -> dict:
    instance: BitShares = shared_bitshares_instance()
    instance.nobroadcast = False
    tx_res = await instance.broadcast(tx)
    return tx_res


async def asset_issue(symbol: str, amount: float, to: str, memo: str = None) -> dict:
    asset: Asset = await Asset(symbol)
    asset.blockchain.nobroadcast = True
    return await asset.issue(amount=amount, to=to, memo=memo)


async def asset_burn(amount: Amount or int or float, symbol: str = None) -> dict:
    instance = shared_bitshares_instance()
    instance.nobroadcast = True
    if not isinstance(amount, Amount) and type(amount) in (int, float):
        amount = await Amount(amount, symbol)
    return await instance.reserve(amount)


async def asset_transfer(
    to: str, amount: float, asset: str, memo: str = None, account: str = None
) -> dict:
    instance = shared_bitshares_instance()
    instance.nobroadcast = True
    if not account:
        account = instance.config["default_account"]
    return await instance.transfer(
        account=account, to=to, amount=amount, asset=asset, memo=memo
    )


async def get_last_op_num(account: str) -> int:
    account_instance = await Account(account)
    history_agen = account_instance.history(limit=1)

    # BitShares have '1.11.1234567890' operationID format so need to retrieve integer ID of operation
    return int([op async for op in history_agen][0]["id"].split(".")[2])


async def wait_new_account_ops(account: str = None, last_op: int = 0) -> list:
    """
    Wait for new operations on (gateway) account

    :param account: bitshares account to parse
    :param last_op: number or last processed operation. It will be NOT included in first cycle iteration
    :return: Reversed iterator of account's operations. Gateway must process operations in order older->newer
    """

    instance = shared_bitshares_instance()
    if not account:
        account = instance.config["default_account"]

    account = await Account(account)

    while True:
        history_agen = account.history(last=last_op)
        new_ops = [op async for op in history_agen]
        if new_ops:
            return list(reversed(new_ops))
        else:
            await asyncio.sleep(BITSHARES_BLOCK_TIME)


async def parse_blocks(start_block_num: int):
    """
    Wait for new blocks in BitShares chain and parse transactions related with gateway

    :param start_block_num: First Block that will be processed. Means that Block with number (start_block_num -1)
                            is already processed
    :return:
    """

    while True:
        try:
            block: Block = await Block(start_block_num)
            if block["transactions"]:
                logging.info(f"Start to parse operations in block {block}")
                # TODO call validate_op()

            start_block_num += 1
        except BlockDoesNotExistsException:
            await asyncio.sleep(BITSHARES_BLOCK_TIME)


async def get_current_block_num():
    bc = await Blockchain(mode="irreversible")
    return await bc.get_current_block_num()


async def read_memo(memo_obj: dict) -> str:
    """Decrypt memo object that was sent with operation TO gateway's account;
        account private memo key must be in the instance's key storage"""
    if memo_obj:
        memo_reader = await Memo()
        return memo_reader.decrypt(memo_obj)


async def validate_op(op: dict) -> BitSharesOperationDTO:
    """Parse BitShares operation body, check order_type, error, etc."""
    instance = shared_bitshares_instance()

    # Check operations types
    # To learn more info about bithsares operationsIDs and types look at:
    # https://github.com/bitshares/python-bitshares/blob/master/bitsharesbase/operationids.py
    op_type = op["op"][0]

    # Transfer type is 0
    if op_type == 0:

        from_account = await Account(op["op"][1]["from"])
        to = await Account(op["op"][1]["to"])
        amount = await Amount(op["op"][1]["amount"])
        asset = await Asset(amount["asset"])
        memo = await read_memo(op["op"][1].get("memo"))

        logging.info(
            f"{from_account.name} transfer {amount} to {to.name} with memo `{memo}`"
        )

        error = TxError.NO_ERROR.value
        status = TxStatus.RECEIVED_NOT_CONFIRMED.value

        # Validate asset
        if asset.symbol != gateway_cfg["gateway_distribute_asset"]:
            error = TxError.BAD_ASSET.value

        # Validate account
        if from_account.name == instance.config["default_account"]:
            order_type = OrderType.DEPOSIT.value
        elif to.name == instance.config["default_account"]:
            order_type = OrderType.WITHDRAWAL.value
        else:
            raise  # Just pretty code, this situation is impossible

        # Validate amount
        if order_type == OrderType.WITHDRAWAL.value:

            if amount < gateway_cfg["gateway_min_withdrawal"]:
                error = TxError.LESS_MIN.value

            if amount > gateway_cfg["gateway_max_withdrawal"]:
                error = TxError.GREATER_MAX.value

            if not memo:
                error = TxError.NO_MEMO.value
            else:
                try:
                    await validate_withdrawal_memo(memo)
                except InvalidMemoMask:
                    error = TxError.FLOOD_MEMO.value

        if order_type == OrderType.DEPOSIT.value:

            if amount < gateway_cfg["gateway_min_deposit"]:
                error = TxError.LESS_MIN.value

            if amount > gateway_cfg["gateway_max_withdrawal"]:
                error = TxError.GREATER_MAX.value

        if error != TxError.NO_ERROR.value:
            status = TxStatus.ERROR.value

        op_dto = BitSharesOperationDTO(
            op_id=int(op["id"].split(".")[2]),
            order_type=order_type,
            asset=asset.symbol,
            from_account=from_account.name,
            to_account=to.name,
            amount=amount.amount,
            block_num=op["block_num"],
            status=status,
            error=error,
        )

        return op_dto


async def validate_withdrawal_memo(memo: str or dict) -> None:
    if isinstance(memo, dict):
        memo = await read_memo(memo)

    if (
        (len(memo.split(":")) != 2)
        or memo.split(":")[0].upper()
        != gateway_cfg["gateway_distribute_asset"].split(".")[1]
        or len(memo.split(":")[1]) == 0
    ):
        raise InvalidMemoMask(f"Flood memo: {memo}")
