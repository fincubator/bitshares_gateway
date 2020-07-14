from src.gateway import *

gw = Gateway()
asyncio.run(gw.main_loop())
