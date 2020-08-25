from typing import Callable, Awaitable, Optional, AbstractSet
import asyncio
from src.utils import get_logger

from aiohttp import (
    ClientWebSocketResponse as HTTPClientWebSocketResponse,
    WSCloseCode as HTTPWSCloseCode,
)
from aiohttp.web import WebSocketResponse as HTTPWebSocketResponse

from booker.rpc.jsonrpc_api import JSONRPCAPIsClient, JSONRPCAPIsServer


log = get_logger("BookerWSJSONRPCAPI")


class WSJSONRPCAPIsClient(JSONRPCAPIsClient):
    stream_constructor: Callable[[], Awaitable[HTTPClientWebSocketResponse]]
    stream: Optional[HTTPClientWebSocketResponse] = None

    def __init__(
        self, stream_constructor: Callable[[], Awaitable[HTTPClientWebSocketResponse]]
    ) -> None:
        super().__init__()

        self.stream_constructor = stream_constructor

    async def _message_send_parent_transport_1(self, request: str) -> str:
        if self.stream is None:
            self.stream = await self.stream_constructor()

        await self.stream.send_str(request)

        response = await self.stream.receive_str()

        return response


class WSJSONRPCAPIsServer(JSONRPCAPIsServer):
    tasks: AbstractSet[Awaitable[bool]]
    new_stream: asyncio.Event

    def __init__(self) -> None:
        super().__init__()

        self.tasks = {*()}
        self.new_stream = asyncio.Event()

    def add_stream(self, stream: HTTPWebSocketResponse) -> Awaitable[None]:
        stream_poller = asyncio.create_task(self.poll_stream(stream))
        self.tasks |= {stream_poller}

        self.new_stream.set()

        return stream_poller

    async def poll_stream(self, ws: HTTPWebSocketResponse) -> None:
        while True:
            try:
                try:
                    request = await ws.receive_str()
                except asyncio.CancelledError:
                    raise
                except BaseException as exception:
                    log.exception(exception)

                    raise exception

                try:
                    response = await self.message_dispatch(request)
                except asyncio.CancelledError:
                    raise
                except BaseException as exception:
                    log.exception(exception)

                    continue

                try:
                    await ws.send_str(response)
                except asyncio.CancelledError:
                    raise
                except BaseException as exception:
                    log.exception(exception)

                    raise exception
            except asyncio.CancelledError:
                log.debug("WebSocket RPC server is stopping.")

                await ws.close(
                    code=HTTPWSCloseCode.GOING_AWAY, message="Connection shutdown"
                )

                log.info("WebSocket RPC server has stopped.")

                raise

    async def poll(self) -> None:
        self.new_stream.clear()

        new_stream = self.new_stream.wait()
        self.tasks |= {asyncio.create_task(new_stream)}

        log.info("WebSocket RPC server has started.")

        while True:
            tasks, self.tasks = self.tasks, {*()}
            done, pending = await asyncio.wait(
                tasks, return_when=asyncio.FIRST_COMPLETED
            )

            self.tasks |= pending

            if new_stream in done:
                self.new_stream.clear()

                new_stream = self.new_stream.wait()
                self.tasks |= {asyncio.create_task(new_stream)}
