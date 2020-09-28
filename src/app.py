import asyncio
import aiohttp
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
    asset_transfer,
    broadcast_tx,
)

from src.db_utils.queries import (
    init_database,
    insert_operation,
    add_gateway_wallet,
    add_operation,
    get_gateway_wallet,
    get_unconfirmed_operations,
    update_last_operation,
    update_operation,
    update_last_parsed_block,
    get_new_ops_for_booker,
    get_pending_operations,
    get_operation_by_hash,
)

from src.db_utils.models import BitsharesOperation, GatewayWallet
from src.gw_dto import (
    BitSharesOperation as BitSharesOperationDTO,
    OrderType,
    TxStatus,
    TxError,
)
from src.bts_ws_rpc_server import BtsWsRPCServer
from src.cryptor import get_wallet_keys, save_wallet_keys, encrypt, decrypt
from src.utils import get_logger, rowproxy_to_dto

from src.config import BITSHARES_BLOCK_TIME, BITSHARES_NEED_CONF, Config

from booker.gateway_api.gateway_side_client import GatewaySideClient
from booker.finteh_proto.dto import (
    OrderDTO,
    TransactionDTO,
    JSONRPCError,
    UpdateOrderDTO,
)

log = get_logger("Gateway")


class AppContext:
    def __init__(self):
        self.cfg = Config()
        self.cfg.with_environment()

        self.booker_cli = GatewaySideClient(
            ctx=self, host=self.cfg.booker_host, port=self.cfg.booker_port
        )
        self.ws_server = BtsWsRPCServer(
            host=self.cfg.http_host, port=self.cfg.http_port, ctx=self
        )

    def unlock_wallet(self):
        account_name = self.cfg.account
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

                await update_last_parsed_block(conn, self.cfg.account, last_block)
                await update_last_operation(conn, self.cfg.account, last_op)

            log.info(f"Retrieve account {self.cfg.account} data from database")
            gateway_wallet = await get_gateway_wallet(conn, self.cfg.account)

            if (gateway_wallet.last_operation is None) or (
                gateway_wallet.last_parsed_block is None
            ):
                raise

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

                op_dto = await validate_op(op, cfg=self.cfg)
                async with self.db.acquire() as conn:
                    async with conn.begin("SERIALIZABLE") as transaction:
                        if op_dto is not None:
                            if op_dto.order_type == OrderType.WITHDRAWAL:
                                # if operation is relevant WITHDRAWAL, add it to database
                                op_to_insert = BitsharesOperation(**op_dto.__dict__)
                                await insert_operation(conn, op_to_insert)
                            else:
                                op_from_db = await get_operation_by_hash(
                                    conn, op_dto.tx_hash
                                )
                                if op_from_db is None:
                                    continue
                                op_from_db_dto = rowproxy_to_dto(
                                    op_from_db,
                                    BitsharesOperation,
                                    BitSharesOperationDTO,
                                )

                                assert not op_from_db_dto.op_id
                                assert op_from_db_dto.block_num == op_dto.block_num

                                op_from_db_dto.op_id = op_dto.op_id
                                op_from_db_dto.status = TxStatus.RECEIVED_NOT_CONFIRMED
                                op_from_db_dto.error = op_dto.error
                                op_from_db_dto.memo = op_dto.memo
                                op_from_db_dto.confirmations = 0
                                op_from_db_dto.tx_created_at = op_dto.tx_created_at

                                op_to_update = BitsharesOperation(
                                    pk=op_from_db["pk"], **op_from_db_dto.__dict__
                                )

                                await update_operation(
                                    conn,
                                    op_to_update,
                                    BitsharesOperation.order_id,
                                    op_to_update.order_id,
                                )

                        # Just refresh last account operations in database
                        await update_last_operation(
                            conn,
                            account_name=self.bitshares_instance.config[
                                "default_account"
                            ],
                            last_operation=op_id,
                        )

    async def notify_booker(self):
        while True:
            async with self.db.acquire() as conn:
                # TODO implement serialization
                new_ops = await get_new_ops_for_booker(conn)

                if len(new_ops) == 0:
                    continue

                for op in new_ops:
                    op_dict = dict(op)
                    op_dict.pop("pk")
                    op_dto = BitSharesOperationDTO(**op_dict)

                    new_tx = TransactionDTO(
                        coin=op_dto.asset,
                        amount=op_dto.amount,
                        from_address=op_dto.from_account,
                        to_address=op_dto.to_account,
                        created_at=op_dto.tx_created_at,
                        confirmations=op_dto.confirmations,
                        max_confirmations=BITSHARES_NEED_CONF,
                        tx_id=f"{op_dto.op_id}:{op_dto.tx_hash}",
                    )

                    order_dto_to_create = OrderDTO(
                        in_tx=new_tx, out_tx=TransactionDTO(to_address=op_dto.memo)
                    )

                    order_dto = await self.booker_cli.create_order_request(
                        order_dto_to_create
                    )

                    try:
                        if hasattr(order_dto, "order_id"):
                            op_dto.order_id = order_dto.order_id
                            op_model = BitsharesOperation(**op_dto.__dict__)
                            await update_operation(
                                conn, op_model, BitsharesOperation.op_id, op_dto.op_id
                            )
                        elif hasattr(order_dto, "message"):
                            log.warning(
                                f"Unable to create order on booker side now: {order_dto.message}"
                            )
                    except Exception as ex:
                        log.warning(f"Unable to create order on booker side now: {ex}")

                await asyncio.sleep(5)

    async def watch_unconfirmed_operations(self):
        """Grep unconfirmed transactions from base and try to confirm it"""
        log.info(f"Watching unconfirmed operations")
        while True:
            async with self.db.acquire() as conn:

                unconfirmed_ops = await get_unconfirmed_operations(conn)
                for op in unconfirmed_ops:

                    op_dto = rowproxy_to_dto(
                        op, BitsharesOperation, BitSharesOperationDTO
                    )
                    is_changed = await confirm_op(op_dto)
                    if is_changed:
                        updated_op = BitsharesOperation(**op_dto.__dict__)
                        await update_operation(
                            conn, updated_op, BitsharesOperation.op_id, updated_op.op_id
                        )

                        updated_tx = TransactionDTO(
                            coin=op_dto.asset,
                            amount=op_dto.amount,
                            tx_id=f"{op_dto.op_id}:{op_dto.tx_hash}",
                            from_address=op_dto.from_account,
                            to_address=op_dto.to_account,
                            created_at=op_dto.tx_created_at,
                            confirmations=op_dto.confirmations,
                            max_confirmations=BITSHARES_NEED_CONF,
                        )

                        if op_dto.order_type == OrderType.DEPOSIT:
                            order_dto_to_update = OrderDTO(
                                order_id=op_dto.order_id, out_tx=updated_tx
                            )
                        elif op_dto.order_type == OrderType.WITHDRAWAL:
                            order_dto_to_update = OrderDTO(
                                order_id=op_dto.order_id, in_tx=updated_tx
                            )
                        else:
                            raise

                        remote_update = await self.booker_cli.update_order_request(
                            order_dto_to_update
                        )

                        if hasattr(remote_update, "is_updated"):
                            log.info(
                                f"Update order {order_dto_to_update.order_id} "
                                f"on booker side: {remote_update.is_updated}"
                            )

            await asyncio.sleep(BITSHARES_BLOCK_TIME)

    async def broadcast_transactions(self):
        """Grep all WAIT-status transaction from database and broatcast it all. If ok, update order on booker"""
        while True:
            async with self.db.acquire() as conn:
                pending_ops = await get_pending_operations(conn)

                for op in pending_ops:

                    op_dto = rowproxy_to_dto(
                        op, BitsharesOperation, BitSharesOperationDTO
                    )

                    _transfer_body = await asset_transfer(
                        account=op_dto.from_account,
                        to=op_dto.to_account,
                        amount=op_dto.amount,
                        asset=op_dto.asset,
                    )

                    transfer = await broadcast_tx(_transfer_body)

                    if transfer:
                        log.info(
                            f"Broadcast {transfer['id']} transaction as part of order {op_dto.order_id} successful"
                        )

                        op_dto.tx_hash = transfer["id"]
                        op_dto.block_num = transfer["block_num"]
                        op_dto.tx_expiration = transfer["expiration"]

                        updated_op = BitsharesOperation(pk=op.pk, **op_dto.__dict__)

                        await update_operation(
                            conn,
                            updated_op,
                            BitsharesOperation.order_id,
                            updated_op.order_id,
                        )

            await asyncio.sleep(1)

    async def watch_blocks(self):
        log.info(f"Parsing blocks...")
        while True:
            await asyncio.sleep(1)
            # await parse_blocks(start_block_num=gateway_wallet.last_parsed_block)

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

        if coro_name == self.notify_booker.__name__:
            coro_to_restart = self.notify_booker

        if coro_to_restart:
            log.info(f"Trying to restart {coro_to_restart.__name__} coroutine")
            loop.create_task(coro_to_restart())

    @staticmethod
    async def shutdown(loop, _signal=None):
        if _signal:
            log.info(f"Received exit signal {_signal.name}...")
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
                s, lambda s=s: asyncio.create_task(self.shutdown(loop, _signal=s))
            )
        loop.set_exception_handler(self.ex_handler)

        if not self.cfg.keys:
            self.unlock_wallet()

        self.db = loop.run_until_complete(init_database(self.cfg))
        self.bitshares_instance = loop.run_until_complete(
            init_bitshares(
                account=self.cfg.account, keys=self.cfg.keys, node=self.cfg.nodes
            )
        )

        loop.run_until_complete(self.synchronize())

        try:
            loop.run_until_complete(
                self.booker_cli.connect(
                    self.cfg.booker_host, self.cfg.booker_port, "/ws-rpc"
                )
            )
            log.info(
                f"BookerClient ready to connect  ws://{self.cfg.booker_host}:{self.cfg.booker_port}/"
            )
            loop.run_until_complete(self.booker_cli.disconnect())
        except Exception as ex:
            log.warning(f"Unable to connect booker: {ex}")

        try:
            loop.run_until_complete(self.ws_server.start())
            log.info(
                f"Started websockets rpc server on ws://{self.cfg.http_host}:{self.cfg.http_port}/ws-rpc"
            )
        except Exception as ex:
            log.warning(f"Unable to start websocker rpc server: {ex}")

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
            loop.create_task(self.notify_booker())
            loop.create_task(self.broadcast_transactions())

            loop.run_forever()
        finally:
            loop.close()
            log.info("Successfully shutdown the app")
