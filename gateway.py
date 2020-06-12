from bitshares_utils import *
from config import gateway_cfg


#  Mock for database and zmq executor module
db_exec = print
zeromq_send = print


async def watch_account_history(bitshares_instance):
    """
    BitShares Gateway account monitoring

    All new operations will be inserted in database and validate. Banker will be notified about it.
    """

    logging.info(f"Watching {bitshares_instance.config['default_account']} for new operations started")

    last_op = 1  # get last op from db

    while True:

        new_ops = await await_new_account_ops(last_op=last_op)
        if not new_ops:
            await asyncio.sleep(1)

        logging.info("Find new ops")
        for op in new_ops:
            # BitShares have '1.11.1234567890' so need to retrieve integer ID of operation
            op_id = op['id'].split('.')[2]

            # Refresh last account operations in database
            db_exec(last_op)

            last_op = op_id

            op_result = await validate_op(op)
            if op_result:
                if op_result:

                    # if operation is relevant, add it to database and tell banker about it
                    db_exec(op_result)
                    zeromq_send(op_result)


async def watch_banker(bitshares_instance):
    """Await Banker"""

    while True:
        logging.info(f"Await for Banker (Booker :P) commands")
        await asyncio.sleep(1)
        # if receive new tx from banker:
            # check it's status
            # add to database with State 0


async def watch_unconfirmed_transactions(bitshares_instance):
    # Grep unconfirmed transactions from base and try to confirm it
    pass


async def gw_loop():
    """Main gateway loop"""
    logging.basicConfig(level=logging.INFO)

    instance = await init_bitshares(account=gateway_cfg["account"],
                                    keys=gateway_cfg["keys"],
                                    node=gateway_cfg['nodes'])
    logging.info(f"Run {gateway_cfg['gateway_core_asset']}.{'gateway_distribute_asset'} bitshares gateway\n"
                 f"distribution account: {instance.config['default_account']}\n"
                 f"Connected to node: {instance.rpc.url}")

    # TODO get settings from control_center

    await asyncio.gather(
        asyncio.create_task(watch_banker(instance)),
        asyncio.create_task(watch_account_history(instance)),
        asyncio.create_task(watch_unconfirmed_transactions(instance))
    )
