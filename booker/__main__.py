import asyncio
import logging

from booker.app import AppContext


logging.basicConfig(level=logging.DEBUG)

context = AppContext()

try:
    asyncio.run(context.run())
except KeyboardInterrupt:
    ...
