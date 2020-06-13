import asyncio
from gateway import *

gw = Gateway()
asyncio.run(gw.main_loop())
