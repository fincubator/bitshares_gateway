from aiohttp import web

from src.utils import get_logger


log = get_logger("HTTP Server")

routes = web.RouteTableDef()


@routes.get("/")
async def is_alive(request):
    log.info(f"Received is_alive request {request.remote}")
    return web.Response(text="Ok")


async def start_http_server(host, port):
    app = web.Application()
    runner = web.AppRunner(app)
    app.add_routes(routes)
    await runner.setup()
    site = web.TCPSite(runner, host, port)
    await site.start()
    log.info(f"Starting http server on http://{host}:{port}/")
