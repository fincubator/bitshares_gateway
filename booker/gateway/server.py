import asyncio
from src.utils import get_logger

from booker.app import AppContext
from booker.gateway.api import process_orders


log = get_logger("BookerGatewayServer")


async def start_server(context: AppContext) -> None:
    log.debug("Orders server is starting.")

    context.tasks |= {asyncio.create_task(process_orders(context))}
