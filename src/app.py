import asyncio
from getpass import getpass
import signal

from rncryptor import DecryptionError

from src.blockchain.bitshares_utils import (
    init_bitshares,
    get_last_op_num,
    get_current_block_num,
    validate_op,
    confirm_op,
    wait_new_account_ops,
)
from src.db_utils.queries import (
    init_database,
    add_gateway_wallet,
    add_operation,
    get_gateway_wallet,
    get_unconfirmed_operations,
    update_last_operation,
    update_operation,
    update_last_parsed_block,
)
from src.db_utils.models import BitsharesOperation, GatewayWallet
from src.gw_dto import BitSharesOperation as BitSharesOperationDTO
from src.cryptor import get_wallet_keys, save_wallet_keys, encrypt, decrypt
from src.utils import get_logger, rowproxy_to_dto
from src.http_server import start_http_server

from src.config import BITSHARES_BLOCK_TIME, Config

# from booker.gateway_api.gateway_side_client import GatewaySideClient
# from booker.gateway_api.gateway_server import GatewayServer
log = get_logger("Gateway")


class AppContext:

    def __init__(self):
        self.cfg = Config()
        self.cfg.with_environment()

    def unlock_wallet(self):
        account_name = self.cfg.account
        active_key = ""
        memo_key = ""

        log.info(f"Try to found encrypted keys of account {account_name}")

        enc_keys = get_wallet_keys(account_name)

        if not enc_keys:
            log.info(f"{account_name} is new account. Let's add and encrypt keys\n")
            memo_key = getpass(f"Please Enter {account_name}'s active private key\n")
            active_key = getpass(f"Ok.\nPlease Enter {account_name}'s memo active key\n")
            password = getpass(
                "Ok\nNow enter password to encrypt keys\n"
                "Warning! Currently there is NO WAY TO RECOVER your password!!! Please be careful!\n"
            )
            password_confirm = getpass("Repeat the password\n")
            if password == password_confirm:
                save_wallet_keys(
                    account_name, encrypt(active_key, password), encrypt(memo_key, password)
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

        self.cfg.keys = [active_key, memo_key]
        del password

    async def synchronize(self):
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

        async with self.db.acquire() as conn:
            wallet = GatewayWallet(account_name=self.cfg.account)
            is_new = await add_gateway_wallet(conn, wallet)
            if is_new:
                log.info(
                    f"Account {self.cfg.account} is new. Let's retrieve data from blockchain and"
                    f" record it in database!"
                )

                last_op = await get_last_op_num(self.cfg.account)
                last_block = await get_current_block_num()

                await update_last_operation(conn, self.cfg.account, last_op)
                await update_last_parsed_block(conn, self.cfg.account, last_block)

            log.info(f"Retrieve account {self.cfg.account} data from database")
            gateway_wallet = await get_gateway_wallet(conn, self.cfg.account)

            log.info(
                f"Start from operation {gateway_wallet.last_operation}, "
                f"block number {gateway_wallet.last_parsed_block}"
            )
            return True


    async def watch_account_history(self):
        """
        BitShares Gateway account monitoring

        All new operations will be validate and insert in database. Booker will be notified about it.
        """

        await self.synchronize()

        log.info(
            f"Watching {self.bitshares_instance.config['default_account']} for new operations started"
        )
        async with self.db.acquire() as conn:
            gateway_wallet = await get_gateway_wallet(conn, self.cfg.account)

        last_op = gateway_wallet.last_operation

        while True:
            new_ops = await wait_new_account_ops(last_op=last_op)
            log.info(f"Found new {len(new_ops)} operations")

            for op in new_ops:
                # BitShares have '1.11.1234567890' so need to retrieve integer ID of operation
                op_id = op["id"].split(".")[2]
                last_op = op_id

                op_result = await validate_op(op, cfg=self.cfg)
                async with self.db.acquire() as conn:

                    if op_result:
                        op_result = BitsharesOperation(**op_result.__dict__)
                        # if operation is relevant, add it to database and tell booker about it
                        await add_operation(conn, op_result)

                        # ctx.ws_booker_client.new_order

                    else:
                        # Just refresh last account operations in database
                        await update_last_operation(
                            conn,
                            account_name=self.bitshares_instance.config["default_account"],
                            last_operation=op_id,
                        )

    async def watch_unconfirmed_operations(self):
        """Grep unconfirmed transactions from base and try to confirm it"""
        log.info(f"Watching unconfirmed operations")
        while True:
            async with self.db.acquire() as conn:

                unconfirmed_ops = await get_unconfirmed_operations(conn)
                for op in unconfirmed_ops:

                    op_dto = rowproxy_to_dto(op, BitsharesOperation, BitSharesOperationDTO)
                    is_changed = await confirm_op(op_dto)
                    if is_changed:
                        updated_op = BitsharesOperation(**op_dto.__dict__)
                        await update_operation(conn, updated_op)
                        # ctx.ws_booker_client.update_order

            await asyncio.sleep(BITSHARES_BLOCK_TIME)

    async def watch_blocks(self):
        log.info(f"Parsing blocks...")
        while True:
            await asyncio.sleep(1)
            # await parse_blocks(start_block_num=gateway_wallet.last_parsed_block)

    async def listen_http(self):
        await start_http_server(self.cfg.http_host, self.cfg.http_port)

    def ex_handler(self, loop, ex_context):
        ex = ex_context.get("exception")
        coro_name = ex_context["future"].get_coro().__name__

        log.exception(f"{ex.__class__.__name__} in {coro_name}: {ex_context}")

        coro_to_restart = None

        if coro_name == self.watch_blocks.__name__:
            coro_to_restart = self.watch_blocks

        if coro_name == self.watch_account_history.__name__:
            coro_to_restart = self.watch_account_history

        if coro_name == self.watch_unconfirmed_operations.__name__:
            coro_to_restart = self.watch_unconfirmed_operations

        if coro_name == self.listen_http.__name__:
            coro_to_restart = self.listen_http

        if coro_to_restart:
            log.info(f"Trying to restart {coro_to_restart.__name__} coroutine")
            loop.create_task(coro_to_restart())

    @staticmethod
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

    def run(self):
        loop = asyncio.get_event_loop()
        signals = (signal.SIGHUP, signal.SIGTERM, signal.SIGINT)
        for s in signals:
            loop.add_signal_handler(
                s, lambda s=s: asyncio.create_task(self.shutdown(loop, signal=s))
            )
        loop.set_exception_handler(self.ex_handler)

        self.db = loop.run_until_complete(init_database(self.cfg))
        self.bitshares_instance = loop.run_until_complete(
            init_bitshares(
                account=self.cfg.account,
                keys=self.cfg.keys,
                node=self.cfg.nodes,
            )
        )

        # self.booker_cli = GatewaySideClient(ctx=self, host=self.cfg.booker_host, port=self.cfg.booker_port)
        try:
            log.info(f"BookerClient ready to connect  ws://{self.cfg.booker_host}:{self.cfg.booker_port}")
        except Exception as ex:
            log.warning(f"Unable to connect booker: {ex}")

        # self.ws_server = GatewayServer(
        #     host=self.cfg.ws_host,
        #     port=self.cfg.ws_port,
        #     ctx=self
        # )
        # loop.run_until_complete(self.ws_server.start())
        log.info(f"Starting websocket server on ws://{self.cfg.ws_host}:{self.cfg.ws_port}/")


        if not self.cfg.is_test_env:
            self.unlock_wallet()

        log.info(
            f"\n"
            f"     Run {self.cfg.gateway_distribute_asset} BitShares gateway\n"
            f"     Distribution account: {self.bitshares_instance.config['default_account']}\n"
            f"     Connected to BitShares API node: {self.bitshares_instance.rpc.url}\n"
            f"     Connected to database: {not self.db.closed}\n"
        )

        try:
            loop.create_task(self.watch_account_history())
            loop.create_task(self.watch_unconfirmed_operations())
            loop.create_task(self.watch_blocks())
            loop.create_task(self.listen_http())

            loop.run_forever()
        finally:
            loop.close()
            log.info("Successfully shutdown the app")
