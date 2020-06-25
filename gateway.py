from bitshares_utils import *
from db_utils.queries import *
from config import gateway_cfg

#  Mock for database and zmq executor module
db_exec = print
zeromq_send = print


class Gateway:
    def __init__(self):
        self.bitshares_instance: BitShares
        self.db: Engine

    async def synchronize_account(self):
        """
        Before start, Gateway should synchronize distributing account's data with database.
        This function fetch last_operation and last_parsed_block from database.

        If account is already in database, Gateway should process all new operations that
        was broadcast till Gateway was shutdown.

        If account is new or it's a first run, Gateway need to add it in database with it's
        last operation number and current irreversible block.

        Warning! Operations and blocks that was broadcast before adding account in database NEVER be processed
        TODO skip_old flag
        """
        async with self.db.acquire() as conn:
            self.gateway_wallet = await get_gateway_wallet(conn, gateway_cfg['account'])
            if not self.gateway_wallet:

                logging.info(f"Account {gateway_cfg['account']} is new. Let's record it in database!")

                last_op = await get_last_op(gateway_cfg['account'])
                last_block = await get_current_block_num()
                await add_gateway_wallet(conn,
                                         account_name=gateway_cfg['account'],
                                         last_operation=last_op,
                                         last_parsed_block=last_block)
                self.gateway_wallet = await get_gateway_wallet(conn, gateway_cfg['account'])
            else:
                logging.info(f"Retrieve account {gateway_cfg['account']} data from database")

                last_op = self.gateway_wallet.last_operation
                last_block = self.gateway_wallet.last_parsed_block

            logging.info(f"Start from operation {last_op}, block number {last_block}")
            if self.gateway_wallet:
                return True
            else: raise

    async def watch_account_history(self):
        """
        BitShares Gateway account monitoring

        All new operations will be inserted in database and validate. Banker will be notified about it.
        """

        logging.info(f"Watching {self.bitshares_instance.config['default_account']} for new operations started")

        last_op = self.gateway_wallet.last_operation

        while True:

            new_ops = await wait_new_account_ops(last_op=last_op)
            if not new_ops:
                await asyncio.sleep(1)

            logging.info("Find new ops")
            for op in new_ops:
                # BitShares have '1.11.1234567890' so need to retrieve integer ID of operation
                op_id = op['id'].split('.')[2]
                last_op = op_id

                # Refresh last account operations in database
                async with self.db.acquire() as conn:
                    await update_last_operation(conn, account_name=self.bitshares_instance.config["default_account"],
                                                last_operation=op_id)

                    op_result = await validate_op(op)
                    if op_result:
                        if op_result:
                            # if operation is relevant, add it to database and tell banker about it
                            db_exec(op_result)
                            zeromq_send(op_result)

    async def watch_banker(self):
        """Await Banker"""

        while True:
            logging.info(f"Await for Banker (Booker :P) commands")
            await asyncio.sleep(1)
            # if receive new tx from banker:
            # check it's status
            # add to database with State 0

    async def watch_unconfirmed_transactions(self):
        # Grep unconfirmed transactions from base and try to confirm it
        pass

    async def watch_blocks(self):
        await parse_blocks(start_block_num=self.gateway_wallet.last_parsed_block)

    async def main_loop(self):
        """Main gateway loop"""
        logging.basicConfig(level=logging.INFO)

        self.db = await init_database()
        self.bitshares_instance = await init_bitshares(account=gateway_cfg["account"],
                                                       keys=gateway_cfg["keys"],
                                                       node=gateway_cfg['nodes'])
        _sync = await self.synchronize_account()
        assert _sync

        logging.info(f"\n"
                     f"     Run {gateway_cfg['gateway_core_asset']}.{gateway_cfg['gateway_distribute_asset']} bitshares gateway\n"
                     f"     Distribution account: {self.bitshares_instance.config['default_account']}\n"
                     f"     Connected to node: {self.bitshares_instance.rpc.url}\n"
                     f"     Connected to database: {not self.db.closed}")

        # TODO get settings from control_center

        await asyncio.gather(
            asyncio.create_task(self.watch_banker()),
            asyncio.create_task(self.watch_account_history()),
            asyncio.create_task(self.watch_blocks()),
            asyncio.create_task(self.watch_unconfirmed_transactions())
        )
