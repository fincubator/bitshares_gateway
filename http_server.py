from aiohttp import web

from utils import get_logger
from config import http_config


log = get_logger("http_server")

routes = web.RouteTableDef()


@routes.get("/")
async def is_alive(request):
    return web.Response(text="Ok")


async def start_http_server():
    app = web.Application()
    runner = web.AppRunner(app)
    app.add_routes(routes)
    await runner.setup()
    site = web.TCPSite(runner, http_config["host"], http_config["port"])
    log.info(
        f"Starting http server on http://{http_config['host']}/{http_config['port']}"
    )
    await site.start()
