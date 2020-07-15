import asyncio
import weakref
from getpass import getpass
from typing import Any, Iterator
import signal

from rncryptor import DecryptionError

from src.bitshares_utils import (
    init_bitshares, get_last_op_num, get_current_block_num, validate_op, confirm_op,
    wait_new_account_ops
)
from src.db_utils.queries import (
    init_database, add_gateway_wallet, add_operation, get_gateway_wallet,
    get_unconfirmed_operations, update_last_operation, update_operation, update_last_parsed_block
)
from src.db_utils.models import BitsharesOperation, GatewayWallet
from src.dto import BitSharesOperation as BitSharesOperationDTO
from src.cryptor import get_wallet_keys, save_wallet_keys, encrypt, decrypt
from src.utils import get_logger, rowproxy_to_dto
from src.http_server import start_http_server

from config import gateway_cfg, BITSHARES_BLOCK_TIME


log = get_logger("Gateway")


class AppContext:
    __slots__ = ("state", "Engine", "BitShares")
    state: dict

    def __init__(self):
        self.state = {}

    def __eq__(self, other: object) -> bool:
        return self is other

    def __getitem__(self, key: str) -> Any:
        return self.state[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.state[key] = value

    def __delitem__(self, key: str) -> None:
        del self.state[key]

    def __len__(self) -> int:
        return len(self.state)

    def __iter__(self) -> Iterator[str]:
        return iter(self.state)

    def add(self, app):
        app_tmp = weakref.ref(app)
        self.state[app.__class__.__name__] = app_tmp

    @property
    def db(self):
        return self.state["Engine"]


def unlock_wallet():
    account_name = gateway_cfg["account"]
    active_key = ""
    memo_key = ""

    log.info(f"Try to found encrypted keys of account {account_name}")

    enc_keys = get_wallet_keys(account_name)

    if not enc_keys:
        log.info(f"{account_name} is new account. Let's add and encrypt keys\n")
        memo_key = getpass(f"Please Enter {account_name}'s active private key\n")
        active_key = getpass(
            f"Ok.\nPlease Enter {account_name}'s memo active key\n"
        )
        password = getpass(
            "Ok\nNow enter password to encrypt keys\n"
            "Warning! Currently there is NO WAY TO RECOVER your password!!! Please be careful!\n"
        )
        password_confirm = getpass("Repeat the password\n")
        if password == password_confirm:
            save_wallet_keys(
                account_name,
                encrypt(active_key, password),
                encrypt(memo_key, password),
            )
            log.info(
                f"Successfully encrypted and stored in file config/.{account_name}.keys"
            )
            del password_confirm
    else:
        while not (active_key and memo_key):
            password = getpass(
                f"Account {account_name} found. Enter password to decrypt keys\n"
            )
            try:
                active_key = decrypt(enc_keys["active"], password)
                memo_key = decrypt(enc_keys["memo"], password)
                log.info(
                    f"Successfully decrypted {account_name} keys:\n"
                    f"active: {active_key[:3] + '...' + active_key[-3:]}\n"
                    f"memo: {memo_key[:3] + '...' + memo_key[-3:]}\n"
                )
            except DecryptionError:
                log.warning("Wrong password!")
            except Exception as ex:
                log.exception(ex)

    gateway_cfg["keys"] = [active_key, memo_key]
    del password


async def synchronize():
    """
    Before start, Gateway should synchronize distributing account's data with database.
    This function fetch last_operation and last_parsed_block from database.

    If account is already in database, Gateway should process all new operations that
    was broadcast till Gateway was shutdown.

    If account is new or it's a first run, Gateway need to add it in database with it's
    last operation number and current irreversible block.

    Warning! Operations and blocks that was broadcast before adding account in database NEVER be processed
    TODO implement skip_old flag ?
    """

    async with ctx.db().acquire() as conn:
        wallet = GatewayWallet(account_name=gateway_cfg["account"])
        is_new = await add_gateway_wallet(conn, wallet)
        if is_new:
            log.info(
                f"Account {gateway_cfg['account']} is new. Let's retrieve data from blockchain and"
                f" record it in database!"
            )

            last_op = await get_last_op_num(gateway_cfg["account"])
            last_block = await get_current_block_num()

            await update_last_operation(conn, gateway_cfg["account"], last_op)
            await update_last_parsed_block(conn, gateway_cfg["account"], last_block)

        log.info(f"Retrieve account {gateway_cfg['account']} data from database")
        gateway_wallet = await get_gateway_wallet(conn, gateway_cfg["account"])

        log.info(
            f"Start from operation {gateway_wallet.last_operation}, "
            f"block number {gateway_wallet.last_parsed_block}"
        )
        return True


async def watch_account_history():
    """
    BitShares Gateway account monitoring

    All new operations will be validate and insert in database. Booker will be notified about it.
    """

    log.info(
        f"Watching {bitshares_instance.config['default_account']} for new operations started"
    )
    async with ctx.db().acquire() as conn:
        gateway_wallet = await get_gateway_wallet(conn, gateway_cfg["account"])

    last_op = gateway_wallet.last_operation

    while True:
        new_ops = await wait_new_account_ops(last_op=last_op)
        log.info(f"Found new {len(new_ops)} operations")

        for op in new_ops:
            # BitShares have '1.11.1234567890' so need to retrieve integer ID of operation
            op_id = op["id"].split(".")[2]
            last_op = op_id

            op_result = await validate_op(op)
            async with ctx.db().acquire() as conn:

                if op_result:
                    op_result = BitsharesOperation(**op_result.__dict__)
                    # if operation is relevant, add it to database and tell banker about it
                    await add_operation(conn, op_result)

                else:
                    # Just refresh last account operations in database
                    await update_last_operation(
                        conn,
                        account_name=bitshares_instance.config[
                            "default_account"
                        ],
                        last_operation=op_id,
                    )


async def watch_unconfirmed_operations():
    """Grep unconfirmed transactions from base and try to confirm it"""
    log.info(f"Watching unconfirmed operations")
    while True:
        async with ctx.db().acquire() as conn:

            unconfirmed_ops = await get_unconfirmed_operations(conn)
            for op in unconfirmed_ops:

                op_dto = rowproxy_to_dto(
                    op, BitsharesOperation, BitSharesOperationDTO
                )
                is_changed = await confirm_op(op_dto)
                if is_changed:
                    updated_op = BitsharesOperation(**op_dto.__dict__)
                    await update_operation(conn, updated_op)

        await asyncio.sleep(BITSHARES_BLOCK_TIME)


async def watch_banker():
    """Await Banker"""
    log.info(f"Await for Booker commands")
    while True:
        await asyncio.sleep(1)


async def watch_blocks():
    log.info(f"Parsing blocks...")
    while True:
        await asyncio.sleep(1)
        # await parse_blocks(start_block_num=gateway_wallet.last_parsed_block)


async def listen_http():
    await start_http_server()
    log.info("Listen HTTP...")


def ex_handler(loop, ex_context):
    ex = ex_context.get("exception")
    coro_name = ex_context["future"].get_coro().__name__

    log.exception(f"{ex.__class__.__name__} in {coro_name}: {ex_context}")

    coro_to_restart = None

    if coro_name == watch_blocks.__name__:
        coro_to_restart = watch_blocks

    if coro_name == watch_banker.__name__:
        coro_to_restart = watch_banker

    if coro_name == watch_account_history.__name__:
        coro_to_restart = watch_account_history

    if coro_name == watch_unconfirmed_operations.__name__:
        coro_to_restart = watch_unconfirmed_operations

    if coro_name == listen_http.__name__:
        coro_to_restart = listen_http

    if coro_to_restart:
        log.info(f"Trying to restart {coro_to_restart.__name__} coroutine")
        loop.create_task(coro_to_restart())


async def shutdown(loop, signal=None):
    if signal:
        log.info(f"Received exit signal {signal.name}...")
    else:
        log.info("No exit signal")

    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]

    [task.cancel() for task in tasks]
    log.info(f"Cancelling {len(tasks)} outstanding tasks")
    await asyncio.gather(*tasks, return_exceptions=True)

    log.info(f"Make some post-shutdown things")
    loop.stop()


loop = asyncio.get_event_loop()
signals = (signal.SIGHUP, signal.SIGTERM, signal.SIGINT)
for s in signals:
    loop.add_signal_handler(
        s, lambda s=s: asyncio.create_task(shutdown(loop, signal=s))
    )
loop.set_exception_handler(ex_handler)

ctx = AppContext()

db = loop.run_until_complete(init_database())
bitshares_instance = loop.run_until_complete(init_bitshares(
        account=gateway_cfg["account"],
        keys=gateway_cfg["keys"],
        node=gateway_cfg["nodes"],
    ))

ctx.add(db)

if not gateway_cfg.get("keys"):
    unlock_wallet()

log.info(
    f"\n"
    f"     Run {gateway_cfg['gateway_distribute_asset']} BitShares gateway\n"
    f"     Distribution account: {bitshares_instance.config['default_account']}\n"
    f"     Connected to node: {bitshares_instance.rpc.url}\n"
    f"     Connected to database: {not db.closed}"
)

try:
    loop.create_task(watch_banker())
    loop.create_task(watch_account_history())
    loop.create_task(watch_unconfirmed_operations())
    loop.create_task(watch_blocks())
    loop.create_task(listen_http())

    loop.run_forever()
finally:
    loop.close()
    log.info("Successfully shutdown the app")
