from bitshares_utils import *
from config import gateway_cfg


#  Mock for database executor module
db = print


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
            last_op = op['id'].split('.')[2]

            op_result = await validate_op(op)
            if op_result:
                db(op_result)


async def outer_loop(bitshares_instance):
    """Await Banker"""

    while True:
        logging.info(f"Await for Banker (Booker :P) commands")
        await asyncio.sleep(1)


async def gw_loop():
    logging.basicConfig(level=logging.INFO)

    instance = await init_bitshares(account=gateway_cfg["account"],
                                    keys=gateway_cfg["keys"],
                                    node=gateway_cfg['nodes'])
    logging.info(f"Run {gateway_cfg['gateway_core_asset']}.{'gateway_distribute_asset'} bitshares gateway\n"
                 f"distribution account: {instance.config['default_account']}\n"
                 f"Connected to node: {instance.rpc.url}")

    await asyncio.gather(
        asyncio.create_task(outer_loop(instance)),
        asyncio.create_task(watch_account_history(instance))
    )


if __name__ == '__main__':
    asyncio.run(gw_loop())
