from typing import Callable, Awaitable, Mapping, Type
import logging

import zmq
from aiozmq import ZmqStream as ZMQStream, create_zmq_stream

from booker.app import AppContext
from booker.rpc.api import APIClient
from booker.rpc.zmq_jsonrpc_api import ZMQJSONRPCAPIsClient


def stream_constructor(
    context: AppContext,
    coin: str
) -> Callable[[], Awaitable[ZMQStream]]:
    async def handler() -> ZMQStream:
        logging.debug('ZeroMQ client is starting.')

        stream = await create_zmq_stream(
            zmq.REQ,
            connect=context.config.gateway_zmq_connection[coin]
        )

        logging.info('ZeroMQ client has started.')

        return stream


    return handler


def construct_clients(
    context: AppContext,
    clients_cls: Mapping[str, Type[APIClient]]
) -> None:
    for coin, client_cls in clients_cls.items():
        apis_client = ZMQJSONRPCAPIsClient(
            stream_constructor=stream_constructor(context, coin)
        )
        context.gateway_zmq_clients[coin] = client_cls(
            apis_client=apis_client
        )
