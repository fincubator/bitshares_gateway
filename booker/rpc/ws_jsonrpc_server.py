from typing import Callable, Awaitable, AbstractSet

import asyncio
import logging

from aiohttp import web
from aiohttp.web import (
    Request as HTTPRequest,
    WebSocketResponse as HTTPWebSocketResponse
)

from booker.app import AppContext
from booker.rpc.api import APIServer
from booker.rpc.ws_jsonrpc_api import WSJSONRPCAPIsServer


def ws_rpc(
    server: WSJSONRPCAPIsServer
) -> Callable[[HTTPRequest], Awaitable[HTTPWebSocketResponse]]:
    async def handler(request: HTTPRequest) -> HTTPWebSocketResponse:
        stream = HTTPWebSocketResponse()

        await stream.prepare(request)

        task = server.add_stream(stream)

        await task

        return stream


    return handler


async def start_server(
    context: AppContext,
    handlers: AbstractSet[APIServer]
) -> None:
    logging.debug('WebSocket RPC server is starting.')

    apis_server = WSJSONRPCAPIsServer()

    for handler in handlers:
        apis_server.api_register(handler)

    context.tasks |= {
        asyncio.create_task(apis_server.poll())
    }

    context.http_app.add_routes([
        web.get('/ws-rpc', ws_rpc(apis_server))
    ])
