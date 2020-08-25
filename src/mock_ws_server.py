from src.ws_booker_api import *
from src.utils import get_logger
import aiohttp


log = get_logger("WS Server")


def using_server(server: WSJSONRPCAPIsServer) -> Callable[[Request], WebSocketResponse]:
    async def handler(request: Request) -> WebSocketResponse:
        stream = WebSocketResponse()

        await stream.prepare(request)

        task = server.add_stream(stream)

        await task

        return stream

    return handler


async def start_gateway_ws_server(ctx) -> None:

    apis_server = WSJSONRPCAPIsServer()

    app = web.Application()
    runner = web.AppRunner(app)
    app.add_routes([web.get("/", using_server(apis_server))])
    await runner.setup()
    site = web.TCPSite(runner, ctx.cfg.ws_host, ctx.cfg.ws_port)
    await site.start()
    log.info(f"Starting rpc server on http://{site._host}:{site._port}/")

    async def bts_booker_client_ws_stream_constructor() -> ClientWebSocketResponse:
        client_ws_stream = await aiohttp.ClientSession().ws_connect(
            f"http://{ctx.cfg.ws_host}:{ctx.cfg.ws_port}"
        )
        return client_ws_stream

    bts_booker_apis_client = WSJSONRPCAPIsClient(
        stream_constructor=bts_booker_client_ws_stream_constructor
    )
    bts_booker_client = MockBookerGatewayOrderAPIClient(
        apis_client=bts_booker_apis_client
    )
    bts_server = BTSServer(booker=bts_booker_client, order_requests=asyncio.Queue())

    apis_server.api_register(bts_server)
    await apis_server.poll()


if __name__ == "__main__":
    from src.app_context_class import AppContext

    ctx = AppContext()

    asyncio.run(start_gateway_ws_server(ctx))
