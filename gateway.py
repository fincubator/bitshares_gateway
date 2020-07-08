from getpass import getpass
from rncryptor import DecryptionError

from bitshares_utils import *
from db_utils.queries import *
from dto import BitSharesOperation as BitSharesOperationDTO
from cryptor import get_wallet_keys, save_wallet_keys, encrypt, decrypt
from utils import get_logger, rowproxy_to_dto
from http_server import start_http_server

from config import gateway_cfg

#  Mock for database and zmq executor module
db_exec = print
zeromq_send = print


log = get_logger("Gateway")


class Gateway:

    bitshares_instance: BitShares
    db: Engine

    def __init__(self):
        pass

    async def unlock_wallet(self):
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
            self.gateway_wallet = await get_gateway_wallet(conn, gateway_cfg["account"])

            log.info(
                f"Start from operation {self.gateway_wallet.last_operation}, "
                f"block number {self.gateway_wallet.last_parsed_block}"
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

        last_op = self.gateway_wallet.last_operation

        while True:

            new_ops = await wait_new_account_ops(last_op=last_op)
            if not new_ops:
                await asyncio.sleep(1)

            log.info(f"Found new {len(new_ops)} operations")

            for op in new_ops:
                # BitShares have '1.11.1234567890' so need to retrieve integer ID of operation
                op_id = op["id"].split(".")[2]
                last_op = op_id

                op_result = await validate_op(op)
                async with self.db.acquire() as conn:

                    if op_result:
                        op_result = BitsharesOperation(**op_result.__dict__)
                        # if operation is relevant, add it to database and tell banker about it
                        await add_operation(conn, op_result)

                    else:
                        # Just refresh last account operations in database
                        await update_last_operation(
                            conn,
                            account_name=self.bitshares_instance.config[
                                "default_account"
                            ],
                            last_operation=op_id,
                        )

    async def watch_unconfirmed_operations(self):
        # Grep unconfirmed transactions from base and try to confirm it
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
                        await update_operation(conn, updated_op)

            await asyncio.sleep(BITSHARES_BLOCK_TIME)

    async def watch_banker(self):
        """Await Banker"""
        log.info(f"Await for Booker commands")
        while True:
            await asyncio.sleep(1)
            # if receive new tx from banker:
            # check it's status
            # add to database with State 0

    async def watch_blocks(self):
        log.info(f"Parsing blocks...")
        pass
        # await parse_blocks(start_block_num=self.gateway_wallet.last_parsed_block)

    async def listen_http(self):
        await start_http_server()
        log.info("Listen HTTP...")

    async def main_loop(self):
        """Main gateway loop"""
        self.db = await init_database()

        if not gateway_cfg.get("keys"):
            await self.unlock_wallet()

        self.bitshares_instance = await init_bitshares(
            account=gateway_cfg["account"],
            keys=gateway_cfg["keys"],
            node=gateway_cfg["nodes"],
        )
        _sync = await self.synchronize()
        assert _sync

        log.info(
            f"\n"
            f"     Run {gateway_cfg['gateway_distribute_asset']} BitShares gateway\n"
            f"     Distribution account: {self.bitshares_instance.config['default_account']}\n"
            f"     Connected to node: {self.bitshares_instance.rpc.url}\n"
            f"     Connected to database: {not self.db.closed}"
        )

        # TODO get settings from control_center

        await asyncio.gather(
            asyncio.create_task(self.watch_banker()),
            asyncio.create_task(self.watch_account_history()),
            asyncio.create_task(self.watch_blocks()),
            asyncio.create_task(self.watch_unconfirmed_operations()),
            asyncio.create_task(self.listen_http()),
        )
