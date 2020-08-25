from typing import Callable, Awaitable, Mapping, Type
from src.utils import get_logger

import aiohttp
from aiohttp import ClientWebSocketResponse as HTTPClientWebSocketResponse

from booker.app import AppContext
from booker.rpc.api import APIClient
from booker.rpc.ws_jsonrpc_api import WSJSONRPCAPIsClient


log = get_logger("BookerWSJSONRPCClient")


def stream_constructor(
    context: AppContext, coin: str
) -> Callable[[], Awaitable[HTTPClientWebSocketResponse]]:
    async def handler() -> HTTPClientWebSocketResponse:
        log.debug("WebSocket RPC client is starting.")

        stream = await aiohttp.ws_connect(context.config.gateway_ws_connection[coin])

        log.info("WebSocket RPC client has started.")

        return stream

    return handler


def construct_clients(
    context: AppContext, clients_cls: Mapping[str, Type[APIClient]]
) -> None:
    for coin, client_cls in clients_cls.items():
        apis_client = WSJSONRPCAPIsClient(
            stream_constructor=stream_constructor(context, coin)
        )
        context.gateway_ws_clients[coin] = client_cls(apis_client=apis_client)
