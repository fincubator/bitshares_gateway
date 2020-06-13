import asyncio
import logging

from bitshares.aio import BitShares
from bitshares.aio.account import Account
from bitshares.aio.asset import Asset
from bitshares.aio.amount import Amount
from bitshares.aio.blockchain import Block, Blockchain
from bitshares.aio.memo import Memo
from bitshares.aio.instance import set_shared_bitshares_instance, shared_bitshares_instance
from graphenecommon.exceptions import BlockDoesNotExistsException

from config import BITSHARES_BLOCK_TIME


async def init_bitshares(account: str = None, node: str or list = None, keys: list = None, loop=None) -> BitShares:
    """ Create bitshares aio.instance, append it to loop and set as shared """
    if not account:
        raise Exception("You need to provide an gateway account. Gateway instance can not work without it!\n"
                        "Check that your account is owner of asset that your instance will distribute!")
    kwargs = dict(node=node, keys=keys, loop=loop, )
    bitshares_instance = BitShares(**kwargs)
    set_shared_bitshares_instance(bitshares_instance)
    await bitshares_instance.connect()
    bitshares_instance.set_default_account(account)
    return bitshares_instance


async def broadcast_tx(tx: dict) -> dict:
    instance: BitShares = shared_bitshares_instance()
    instance.nobroadcast = False
    tx_res = await instance.broadcast(tx)
    return tx_res


async def asset_issue(symbol: str, amount: float, to: str, **kwargs) -> dict:
    asset: Asset = await Asset(symbol)
    asset.blockchain.nobroadcast = True
    return await asset.issue(amount=amount, to=to, **kwargs)


async def asset_burn(amount: Amount or int or float,
                     symbol: str = None, **kwargs) -> dict:
    instance = shared_bitshares_instance()
    instance.nobroadcast = True
    if not isinstance(amount, Amount) and type(amount) in (int, float):
        amount = await Amount(amount, symbol)
    return await instance.reserve(amount, **kwargs)


async def asset_transfer(**kwargs) -> dict:
    instance = shared_bitshares_instance()
    instance.nobroadcast = True
    return await instance.transfer(**kwargs)


async def wait_new_account_ops(account: str = None, last_op: int = 0) -> list:
    """
    Wait for new operations on (gateway) account

    :param account: bitshares account to parse
    :param last_op: number or last processed operation. It will be NOT included in first cycle iteration
    :return: Reversed iterator of account's operations. Gateway must process operations in order older->newer
    """

    instance = shared_bitshares_instance()
    if not account:
        account = instance.config['default_account']

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


async def validate_op(op: dict):
    """Parse BitShares operation and process it"""

    # Check operations types
    # for more info about bithsares operationsIds:
    # https://github.com/bitshares/python-bitshares/blob/master/bitsharesbase/operationids.py
    op_type = op['op'][0]

    # Transfer type is 0
    if op_type == 0:

        from_user = await Account(op['op'][1]['from'])
        to = await Account(op['op'][1]['to'])
        amount = await Amount(op['op'][1]['amount'])
        memo = await read_memo(op['op'][1].get('memo'))

        # This should be just logging, need to return JSON Schema instance with op_data
        return f"{from_user.name} transfer {amount} to {to.name} with memo `{memo}`"

    # Issue asset type is 14
    elif op_type == 14:
        issuer = await Account(op['op'][1]['issuer'])
        amount = await Amount(op['op'][1]['asset_to_issue'])
        issue_to_account = await Account(op['op'][1]['issue_to_account'])
        memo = await read_memo(op['op'][1].get('memo'))

        # This should be just logging, need to return JSON Schema instance with op_data
        return f"{issuer.name} issue {amount} to {issue_to_account.name} with memo `{memo}`"

    # Asset burn type is 15
    elif op_type == 15:
        amount_to_reserve = await Amount(op['op'][1]['amount_to_reserve'])
        payer = await Account(op['op'][1]['payer'])
        return f"{payer.name} burn {amount_to_reserve}"

    # Any other types of operations are not interested. Return only int
    else:
        return


async def get_last_op(account: str) -> int:
    account_instance = await Account(account)
    history_agen = account_instance.history(limit=1)

    # BitShares have '1.11.1234567890' operationID format so need to retrieve integer ID of operation
    return int([op async for op in history_agen][0]['id'].split('.')[2])
