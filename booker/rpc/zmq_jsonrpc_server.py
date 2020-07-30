from typing import AbstractSet

import asyncio
import logging

import zmq
from aiozmq import create_zmq_stream

from booker.app import AppContext
from booker.rpc.api import APIServer
from booker.rpc.zmq_jsonrpc_api import ZMQJSONRPCAPIsServer


async def start_server(
    context: AppContext,
    handlers: AbstractSet[APIServer]
) -> None:
    logging.debug('ZeroMQ RPC server is starting.')

    server_stream = await create_zmq_stream(
        zmq.REP,
        bind=(f'{context.config.zmq_proto}://{context.config.zmq_host}:'
              f'{context.config.zmq_port}')
    )
    apis_server = ZMQJSONRPCAPIsServer(stream=server_stream)

    for handler in handlers:
        apis_server.api_register(handler)

    context.tasks |= {
        asyncio.create_task(apis_server.poll())
    }
