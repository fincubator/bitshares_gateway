from typing import Callable, Awaitable, Optional
import asyncio
from src.utils import get_logger

from aiozmq import ZmqStream as ZMQStream

from booker.rpc.jsonrpc_api import JSONRPCAPIsClient, JSONRPCAPIsServer


log = get_logger("BookerZMQJSONRPCApi")


class ZMQJSONRPCAPIsClient(JSONRPCAPIsClient):
    stream_constructor: Callable[[], Awaitable[ZMQStream]]
    stream: Optional[ZMQStream] = None

    def __init__(self, stream_constructor: Callable[[], Awaitable[ZMQStream]]) -> None:
        super().__init__()

        self.stream_constructor = stream_constructor

    async def _message_send_parent_transport_1(self, request: str) -> str:
        if self.stream is None:
            self.stream = await self.stream_constructor()

        data_request = [request.encode("ascii")]

        self.stream.write(data_request)

        data_response = await self.stream.read()
        response = data_response[0]

        return response


class ZMQJSONRPCAPIsServer(JSONRPCAPIsServer):
    stream: ZMQStream

    def __init__(self, stream: ZMQStream) -> None:
        super().__init__()

        self.stream = stream

    async def poll(self) -> None:
        log.info("ZeroMQ RPC server has started.")

        while True:
            try:
                try:
                    data_request = await self.stream.read()
                except asyncio.CancelledError:
                    raise
                except BaseException as exception:
                    log.exception(exception)

                    raise exception

                try:
                    request = data_request[0]
                    response = await self.message_dispatch(request)
                    data_response = [response.encode("ascii")]
                except asyncio.CancelledError:
                    raise
                except BaseException as exception:
                    log.exception(exception)

                    continue

                try:
                    self.stream.write(data_response)
                except asyncio.CancelledError:
                    raise
                except BaseException as exception:
                    log.exception(exception)

                    raise exception
            except asyncio.CancelledError:
                log.debug("ZeroMQ RPC server is stopping.")

                self.stream.close()

                log.info("ZeroMQ RPC server has stopped.")

                raise
