from typing import Optional, AbstractSet, Mapping

import asyncio
from src.utils import get_logger

from aiopg.sa import Engine as DBEngine, create_engine as create_db_engine
from aiohttp.web import Application as HTTPApp, RouteTableDef as HTTPRouteTableDef

from booker.config import Config
from booker.rpc.gateway.api import AbstractGatewayBookerOrderAPIClient


log = get_logger("BookerApp")


class AppContext:
    config: Config
    db_engine: Optional[DBEngine] = None
    http_app: HTTPApp
    http_task: Optional[asyncio.Task] = None
    tasks: AbstractSet[asyncio.Task]
    gateway_ws_clients: Mapping[str, AbstractGatewayBookerOrderAPIClient]
    gateway_zmq_clients: Mapping[str, AbstractGatewayBookerOrderAPIClient]

    def __init__(self) -> None:
        super().__init__()

        self.config = Config()
        self.http_app = HTTPApp()
        self.tasks = {*()}
        self.gateway_ws_clients = {}
        self.gateway_zmq_clients = {}

    @property
    def gateway_clients(self) -> Mapping[str, AbstractGatewayBookerOrderAPIClient]:
        gateway_clients = None

        if self.config.client_transport == "ws":
            gateway_clients = self.gateway_ws_clients
        elif self.config.client_transport == "zmq":
            gateway_clients = self.gateway_zmq_clients

        assert gateway_clients != None

        return gateway_clients

    async def run(self) -> None:
        from booker.http.handlers import construct_handlers as construct_http_handlers
        from booker.http.server import start_server as start_http_server
        from booker.rpc.gateway.handlers import BookerGatewayOrderAPIServer
        from booker.rpc.gateway.client import GatewayBookerOrderAPIClient
        from booker.rpc.ws_jsonrpc_server import start_server as start_ws_jsonrpc_server
        from booker.rpc.zmq_jsonrpc_server import (
            start_server as start_zmq_jsonrpc_server,
        )
        from booker.rpc.ws_jsonrpc_client import (
            construct_clients as construct_ws_jsonrpc_clients,
        )
        from booker.rpc.zmq_jsonrpc_client import (
            construct_clients as construct_zmq_jsonrpc_clients,
        )
        from booker.gateway.server import start_server as start_process_orders_server

        log.debug("The database connection is opening.")

        self.db_engine = await create_db_engine(
            host=self.config.db_host,
            port=self.config.db_port,
            user=self.config.db_user,
            password=self.config.db_password,
            database=self.config.db_database,
        )

        log.info("The database connection has opened.")

        rpc_clients = {
            "ETH": GatewayBookerOrderAPIClient,
            "BTS": GatewayBookerOrderAPIClient,
        }

        construct_ws_jsonrpc_clients(self, rpc_clients)
        construct_zmq_jsonrpc_clients(self, rpc_clients)

        rpc_handlers = {BookerGatewayOrderAPIServer(context=self)}

        await asyncio.gather(
            start_ws_jsonrpc_server(self, rpc_handlers),
            start_zmq_jsonrpc_server(self, rpc_handlers),
        )

        http_handlers = HTTPRouteTableDef()

        construct_http_handlers(self, http_handlers)
        await start_http_server(self, http_handlers)
        await start_process_orders_server(self)

        cancel_signal = asyncio.Event()

        try:
            await asyncio.wait({asyncio.create_task(cancel_signal.wait())})
        finally:
            self.http_task.cancel()
            await self.http_task

            for task in self.tasks:
                task.cancel()

            await asyncio.wait(self.tasks)

            log.debug("The database connection is closing.")

            self.db_engine.close()
            await self.db_engine.wait_closed()

            log.info("The database connection has closed.")

            raise
