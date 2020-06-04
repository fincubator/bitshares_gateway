import asyncio
import logging

from bitshares.aio import BitShares
from bitshares.aio.account import Account
from bitshares.aio.asset import Asset
from bitshares.aio.amount import Amount
from bitshares.aio.memo import Memo
from bitshares.aio.instance import set_shared_bitshares_instance, shared_bitshares_instance

from config import BITSHARES_BLOCK_TIME


logging.basicConfig(level=logging.INFO)


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


async def await_new_account_ops(account: str = None, last_op: int = 0) -> list:
    """Wait for new operations on (gateway) account"""

    instance = shared_bitshares_instance()
    if not account:
        account = instance.config['default_account']

    account = await Account(account)

    while True:
        history_agen = account.history(last=last_op)
        new_ops = [op async for op in history_agen]
        if new_ops:
            return new_ops
        else:
            await asyncio.sleep(BITSHARES_BLOCK_TIME)


async def read_memo(memo_obj: dict) -> str:
    """Decrypt memo object that was sent with operation TO gateway's account;
        account private memo key must be in the instance's key storage"""

    memo_reader = await Memo()
    return memo_reader.decrypt(memo_obj)
