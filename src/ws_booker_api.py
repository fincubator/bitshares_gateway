from src.blockchain.bitshares_utils import init_bitshares, validate_bitshares_account
from src.config import Config

from aiohttp.web import Application, Request, WebSocketResponse
from aiohttp import web, ClientWebSocketResponse
from typing import Optional, Mapping, Callable
import asyncio
from uuid import UUID

from marshmallow_dataclass import dataclass

from booker.dto import DataTransferClass, Amount
from booker.rpc.api import APIStream, api_method, api_client, api_server
from booker.rpc.ws_jsonrpc_api import WSJSONRPCAPIsClient, WSJSONRPCAPIsServer
from booker.gateway.dto import (
    OrderType,
    TxError,
    ValidateAddress,
    ValidatedAddress,
    GetDepositAddress,
    DepositAddress,
    NewInOrder,
    NewOutOrder,
    NewInOrderRequest,
    NewInTxOrder,
    NewOutTxOrder,
    UpdateTxOrder,
)
from booker.rpc.gateway.api import (
    AbstractBookerGatewayOrderAPI,
    AbstractBookerGatewayOrderAPIServer,
    AbstractGatewayBookerOrderAPI,
    AbstractGatewayBookerOrderAPIClient,
)


cfg = Config()


@dataclass
class Tx(DataTransferClass):
    tx_id: UUID
    tx_coin: str
    tx_hash: Optional[str] = None
    tx_from: Optional[str] = None
    tx_to: Optional[str] = None
    tx_amount: Optional[Amount] = None
    tx_created_at: Optional[int] = None
    tx_error: TxError = TxError.NO_ERROR
    tx_confirmations: int = 0
    tx_max_confirmations: int = 0
    memo_to: Optional[str] = None


@dataclass
class Order(DataTransferClass):
    order_id: UUID
    order_type: OrderType
    in_tx: Tx
    out_tx: Tx


class BookerApp:
    txs: Mapping[UUID, Tx] = {}
    orders: Mapping[UUID, Order] = {}


@api_client
class AbstractBookerGatewayOrderAPIClient(AbstractBookerGatewayOrderAPI):
    ...


class MockBookerGatewayOrderAPIClient(AbstractBookerGatewayOrderAPIClient):
    ...


class MockBookerGatewayOrderAPIServer(AbstractBookerGatewayOrderAPIServer):
    booker: BookerApp
    step: int = 0

    def __init__(self, booker: BookerApp) -> None:
        super().__init__()

        self.booker = booker

    @api_method
    async def new_in_order_request(
        self, args: NewInOrderRequest
    ) -> APIStream[None, None]:
        yield None

    @api_method
    async def new_in_tx_order(self, args: NewInTxOrder) -> APIStream[None, None]:
        yield None

    @api_method
    async def update_in_tx_order(self, args: UpdateTxOrder) -> APIStream[None, None]:
        yield None

    @api_method
    async def new_out_tx_order(self, args: NewOutTxOrder) -> APIStream[None, None]:
        yield None

    @api_method
    async def update_out_tx_order(self, args: UpdateTxOrder) -> APIStream[None, None]:
        yield None


@api_server
class GatewayBookerOrderAPIServer(AbstractGatewayBookerOrderAPI):
    ...


class BTSClient(AbstractGatewayBookerOrderAPIClient):
    ...


class BTSServer(GatewayBookerOrderAPIServer):
    """Receiving commands from Booker instance with websockets and process it"""

    booker: AbstractBookerGatewayOrderAPIClient
    txs: Mapping[UUID, Tx] = {}
    orders: Mapping[UUID, Order] = {}
    order_requests: asyncio.Queue()
    step: int = 0

    def __init__(
        self,
        booker: AbstractBookerGatewayOrderAPIClient,
        order_requests: asyncio.Queue(),
    ) -> None:
        super().__init__()

        self.booker = booker
        self.order_requests = order_requests

    @api_method
    async def validate_address(
        self, args: ValidateAddress
    ) -> APIStream[ValidatedAddress, None]:

        await init_bitshares(account=cfg.account, node=cfg.nodes, keys=cfg.keys)
        is_valid = await validate_bitshares_account(args.tx_to)

        yield ValidatedAddress(valid=is_valid)

    @api_method
    async def get_deposit_address(
        self, args: GetDepositAddress
    ) -> APIStream[DepositAddress, None]:
        yield DepositAddress(tx_to=cfg.account)

    @api_method
    async def new_in_order(self, args: NewInOrder) -> APIStream[None, None]:
        await self.order_requests.put(args)

        yield None

    @api_method
    async def new_out_order(self, args: NewOutOrder) -> APIStream[None, None]:
        await self.order_requests.put(args)

        yield None

    def process_in_order_request(self, order: NewInOrder) -> None:
        pass

    def process_out_order_request(self, order: NewOutOrder) -> None:
        pass

    async def process_database_order(self) -> None:
        pass

    async def process_orders(self) -> None:
        pass
