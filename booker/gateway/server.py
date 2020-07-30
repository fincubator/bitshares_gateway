import asyncio
import logging

from booker.app import AppContext
from booker.gateway.api import process_orders


async def start_server(context: AppContext) -> None:
    logging.debug('Orders server is starting.')

    context.tasks |= {asyncio.create_task(process_orders(context))}
