import pytest

from typing import Optional, Mapping, Callable
import asyncio
from uuid import UUID
from decimal import Decimal
from copy import deepcopy

from marshmallow_dataclass import dataclass
from aiohttp import ClientWebSocketResponse, web
from aiohttp.web import Application, Request, WebSocketResponse
from aiohttp.test_utils import TestClient, TestServer

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


new_deposit_in_order = NewInOrder(
    order_id=UUID("36aa16d4-e5b3-4c26-8f33-fee982ea02cc"),
    order_type=OrderType.DEPOSIT,
    in_tx_coin="USDT",
    in_tx_to="0x8901c9bF56581513a158eEf00794FBb0D698f2Ed",
    in_tx_amount=Decimal("0"),
    out_tx_coin="FINTEH.USDT",
    out_tx_to="kwaskoff",
)


new_eth_in_tx = Tx(
    tx_id=UUID("18f7d676-b20e-4b0b-ba5a-b3617736e938"),
    tx_coin=new_deposit_in_order.in_tx_coin,
    tx_to=new_deposit_in_order.in_tx_to,
    tx_amount=new_deposit_in_order.in_tx_amount,
)


eth_in_tx_0 = deepcopy(new_eth_in_tx)
eth_in_tx_0.tx_from = "0xE05c4f7d6e1c774E42B0ca6C833d008467fd361A"
eth_in_tx_0.tx_hash = (
    "0xcb164a9f2a66d2f8c564cd5eaaed5a3415cd87af03abcc8278a183eeaceaf38f"
)
eth_in_tx_0.tx_amount = Decimal("50")
eth_in_tx_0.tx_created_at = 1594394720
eth_in_tx_0.tx_confirmations += 1
eth_in_tx_0.tx_max_confirmations = 3


new_eth_in_tx_order = NewInTxOrder(
    order_id=new_deposit_in_order.order_id,
    tx_hash=eth_in_tx_0.tx_hash,
    tx_from=eth_in_tx_0.tx_from,
    tx_amount=eth_in_tx_0.tx_amount,
    tx_created_at=eth_in_tx_0.tx_created_at,
    tx_error=eth_in_tx_0.tx_error,
    tx_confirmations=eth_in_tx_0.tx_confirmations,
    tx_max_confirmations=eth_in_tx_0.tx_max_confirmations,
)


eth_in_tx_1 = deepcopy(eth_in_tx_0)
eth_in_tx_1.tx_confirmations += 1


update_eth_in_tx_order_0 = UpdateTxOrder(
    order_id=new_deposit_in_order.order_id,
    tx_error=eth_in_tx_1.tx_error,
    tx_confirmations=eth_in_tx_1.tx_confirmations,
    tx_max_confirmations=eth_in_tx_1.tx_max_confirmations,
)


eth_in_tx_2 = deepcopy(eth_in_tx_1)
eth_in_tx_2.tx_confirmations += 1


update_eth_in_tx_order_1 = UpdateTxOrder(
    order_id=new_deposit_in_order.order_id,
    tx_error=eth_in_tx_2.tx_error,
    tx_confirmations=eth_in_tx_2.tx_confirmations,
    tx_max_confirmations=eth_in_tx_2.tx_max_confirmations,
)


new_deposit_out_order = NewOutOrder(
    order_id=new_deposit_in_order.order_id,
    order_type=new_deposit_in_order.order_type,
    in_tx_coin=new_deposit_in_order.in_tx_coin,
    in_tx_hash=eth_in_tx_2.tx_hash,
    in_tx_from=eth_in_tx_2.tx_from,
    in_tx_to=new_deposit_in_order.in_tx_to,
    in_tx_amount=eth_in_tx_2.tx_amount,
    in_tx_created_at=eth_in_tx_2.tx_created_at,
    in_tx_error=eth_in_tx_2.tx_error,
    in_tx_confirmations=eth_in_tx_2.tx_confirmations,
    in_tx_max_confirmations=eth_in_tx_2.tx_max_confirmations,
    out_tx_coin=new_deposit_in_order.out_tx_coin,
    out_tx_to=new_deposit_in_order.out_tx_to,
)


new_bts_out_tx = Tx(
    tx_id=UUID("b78f2cdb-0d8b-479d-8074-9784cb673a0d"),
    tx_coin=new_deposit_out_order.out_tx_coin,
    tx_to=new_deposit_out_order.out_tx_to,
)


bts_out_tx_0 = deepcopy(new_bts_out_tx)
bts_out_tx_0.tx_from = "finteh-usdt"
bts_out_tx_0.tx_hash = "738bc2bd32e2da31f587d281aa7ee9bd02b9daf0:0"
bts_out_tx_0.tx_amount = Decimal("50")
bts_out_tx_0.tx_created_at = 1594394731
bts_out_tx_0.tx_confirmations += 1
bts_out_tx_0.tx_max_confirmations = 3


new_bts_out_tx_order = NewOutTxOrder(
    order_id=new_deposit_out_order.order_id,
    tx_hash=bts_out_tx_0.tx_hash,
    tx_from=bts_out_tx_0.tx_from,
    tx_amount=bts_out_tx_0.tx_amount,
    tx_created_at=bts_out_tx_0.tx_created_at,
    tx_error=bts_out_tx_0.tx_error,
    tx_confirmations=bts_out_tx_0.tx_confirmations,
    tx_max_confirmations=bts_out_tx_0.tx_max_confirmations,
)


bts_out_tx_1 = deepcopy(bts_out_tx_0)
bts_out_tx_1.tx_confirmations += 1


update_bts_out_tx_order_0 = UpdateTxOrder(
    order_id=new_deposit_out_order.order_id,
    tx_error=bts_out_tx_1.tx_error,
    tx_confirmations=bts_out_tx_1.tx_confirmations,
    tx_max_confirmations=bts_out_tx_1.tx_max_confirmations,
)


bts_out_tx_2 = deepcopy(bts_out_tx_1)
bts_out_tx_2.tx_confirmations += 1


update_bts_out_tx_order_1 = UpdateTxOrder(
    order_id=new_deposit_out_order.order_id,
    tx_error=bts_out_tx_2.tx_error,
    tx_confirmations=bts_out_tx_2.tx_confirmations,
    tx_max_confirmations=bts_out_tx_2.tx_max_confirmations,
)


new_withdrawal_in_order = NewInOrder(
    order_id=UUID("ee1af642-d003-435b-8ea9-88b86849bb82"),
    order_type=OrderType.WITHDRAWAL,
    in_tx_coin="FINTEH.USDT",
    in_tx_to="finteh-usdt",
    in_tx_amount=Decimal("50"),
    out_tx_coin="USDT",
)


new_bts_in_tx = Tx(
    tx_id=UUID("387bff73-9d47-4a02-a9b8-20416a4bc212"),
    tx_coin=new_withdrawal_in_order.in_tx_coin,
    tx_to=new_withdrawal_in_order.in_tx_to,
    tx_amount=new_withdrawal_in_order.in_tx_amount,
)


bts_in_tx_0 = deepcopy(new_bts_in_tx)
bts_in_tx_0.tx_from = "kwaskoff"
bts_in_tx_0.tx_hash = "438bc2bd32e2da76f437d281aa7af9bd02b37af0:0"
bts_in_tx_0.tx_amount = Decimal("50")
bts_in_tx_0.tx_created_at = 1594403342
bts_in_tx_0.tx_confirmations += 1
bts_in_tx_0.tx_max_confirmations = 3
bts_in_tx_0.memo_to = "0x2d6F329Da0e983288E57DBca1e496dd60fae5437"


new_bts_in_tx_order = NewInTxOrder(
    order_id=new_withdrawal_in_order.order_id,
    tx_hash=bts_in_tx_0.tx_hash,
    tx_from=bts_in_tx_0.tx_from,
    tx_amount=bts_in_tx_0.tx_amount,
    tx_created_at=bts_in_tx_0.tx_created_at,
    tx_error=bts_in_tx_0.tx_error,
    tx_confirmations=bts_in_tx_0.tx_confirmations,
    tx_max_confirmations=bts_in_tx_0.tx_max_confirmations,
    memo_to=bts_in_tx_0.memo_to,
)


bts_in_tx_1 = deepcopy(bts_in_tx_0)
bts_in_tx_1.tx_confirmations += 1


update_bts_in_tx_order_0 = UpdateTxOrder(
    order_id=new_withdrawal_in_order.order_id,
    tx_error=bts_in_tx_1.tx_error,
    tx_confirmations=bts_in_tx_1.tx_confirmations,
    tx_max_confirmations=bts_in_tx_1.tx_max_confirmations,
)


bts_in_tx_2 = deepcopy(bts_in_tx_1)
bts_in_tx_2.tx_confirmations += 1


update_bts_in_tx_order_1 = UpdateTxOrder(
    order_id=new_withdrawal_in_order.order_id,
    tx_error=bts_in_tx_2.tx_error,
    tx_confirmations=bts_in_tx_2.tx_confirmations,
    tx_max_confirmations=bts_in_tx_2.tx_max_confirmations,
)


new_withdrawal_out_order = NewOutOrder(
    order_id=new_withdrawal_in_order.order_id,
    order_type=new_withdrawal_in_order.order_type,
    in_tx_coin=new_withdrawal_in_order.in_tx_coin,
    in_tx_hash=bts_in_tx_2.tx_hash,
    in_tx_from=bts_in_tx_2.tx_from,
    in_tx_to=new_withdrawal_in_order.in_tx_to,
    in_tx_amount=bts_in_tx_2.tx_amount,
    in_tx_created_at=bts_in_tx_2.tx_created_at,
    in_tx_error=bts_in_tx_2.tx_error,
    in_tx_confirmations=bts_in_tx_2.tx_confirmations,
    in_tx_max_confirmations=bts_in_tx_2.tx_max_confirmations,
    out_tx_coin=new_withdrawal_in_order.out_tx_coin,
    out_tx_to=new_bts_in_tx_order.memo_to,
)


new_eth_out_tx = Tx(
    tx_id=UUID("a4b44708-36bd-4483-b115-42260b0fdb77"),
    tx_coin=new_withdrawal_out_order.out_tx_coin,
    tx_to=new_withdrawal_out_order.out_tx_to,
)


eth_out_tx_0 = deepcopy(new_eth_out_tx)
eth_out_tx_0.tx_from = "0xb6f121Df61ae04D8cb3978BE035C004b24B44283"
eth_out_tx_0.tx_hash = (
    "0x684c875217a5a68406aba4cc710f57348c1afe9b27fb244675f987d5e337e019"
)
eth_out_tx_0.tx_amount = Decimal("50")
eth_out_tx_0.tx_created_at = 1594403353
eth_out_tx_0.tx_confirmations += 1
eth_out_tx_0.tx_max_confirmations = 3


new_eth_out_tx_order = NewOutTxOrder(
    order_id=new_withdrawal_out_order.order_id,
    tx_hash=eth_out_tx_0.tx_hash,
    tx_from=eth_out_tx_0.tx_from,
    tx_amount=eth_out_tx_0.tx_amount,
    tx_created_at=eth_out_tx_0.tx_created_at,
    tx_error=eth_out_tx_0.tx_error,
    tx_confirmations=eth_out_tx_0.tx_confirmations,
    tx_max_confirmations=eth_out_tx_0.tx_max_confirmations,
)


eth_out_tx_1 = deepcopy(eth_out_tx_0)
eth_out_tx_1.tx_confirmations += 1


update_eth_out_tx_order_0 = UpdateTxOrder(
    order_id=new_withdrawal_out_order.order_id,
    tx_error=eth_out_tx_1.tx_error,
    tx_confirmations=eth_out_tx_1.tx_confirmations,
    tx_max_confirmations=eth_out_tx_1.tx_max_confirmations,
)


eth_out_tx_2 = deepcopy(eth_out_tx_1)
eth_out_tx_2.tx_confirmations += 1


update_eth_out_tx_order_1 = UpdateTxOrder(
    order_id=new_withdrawal_out_order.order_id,
    tx_error=eth_out_tx_2.tx_error,
    tx_confirmations=eth_out_tx_2.tx_confirmations,
    tx_max_confirmations=eth_out_tx_2.tx_max_confirmations,
)


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


class MockETHGatewayBookerOrderAPIClient(AbstractGatewayBookerOrderAPIClient):
    ...


class MockETHGatewayBookerOrderAPIServer(GatewayBookerOrderAPIServer):
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
        yield ValidatedAddress(valid=True)

    @api_method
    async def get_deposit_address(
        self, args: GetDepositAddress
    ) -> APIStream[DepositAddress, None]:
        if args.out_tx_to is None:
            raise ValueError("Unknown address")

        if args.out_tx_to == "kwaskoff":
            yield DepositAddress(tx_to="0x8901c9bF56581513a158eEf00794FBb0D698f2Ed")
        else:
            raise ValueError("Unknown address")

    @api_method
    async def new_in_order(self, args: NewInOrder) -> APIStream[None, None]:
        await self.order_requests.put(args)

        yield None

    @api_method
    async def new_out_order(self, args: NewOutOrder) -> APIStream[None, None]:
        await self.order_requests.put(args)

        yield None

    def process_in_order_request(self, order: NewInOrder) -> None:
        assert order == new_deposit_in_order

        eth_in_tx = Tx(
            tx_id=UUID("18f7d676-b20e-4b0b-ba5a-b3617736e938"),
            tx_coin=order.in_tx_coin,
            tx_to=order.in_tx_to,
            tx_amount=order.in_tx_amount,
        )

        assert eth_in_tx == new_eth_in_tx

        bts_out_tx = Tx(
            tx_id=UUID("b78f2cdb-0d8b-479d-8074-9784cb673a0d"),
            tx_coin=order.out_tx_coin,
            tx_to=order.out_tx_to,
        )

        assert bts_out_tx == new_bts_out_tx

        self.txs[eth_in_tx.tx_id] = eth_in_tx
        self.txs[bts_out_tx.tx_id] = bts_out_tx
        self.orders[order.order_id] = Order(
            order_id=order.order_id,
            order_type=order.order_type,
            in_tx=eth_in_tx,
            out_tx=bts_out_tx,
        )

    def process_out_order_request(self, order: NewOutOrder) -> None:
        assert order == new_withdrawal_out_order

        bts_in_tx = Tx(
            tx_id=UUID("387bff73-9d47-4a02-a9b8-20416a4bc212"),
            tx_coin=order.in_tx_coin,
            tx_hash=order.in_tx_hash,
            tx_from=order.in_tx_from,
            tx_to=order.in_tx_to,
            tx_amount=order.in_tx_amount,
            tx_created_at=order.in_tx_created_at,
            tx_error=order.in_tx_error,
            tx_confirmations=order.in_tx_confirmations,
            tx_max_confirmations=order.in_tx_max_confirmations,
            memo_to=order.out_tx_to,
        )

        assert bts_in_tx == bts_in_tx_2

        eth_out_tx = Tx(
            tx_id=UUID("a4b44708-36bd-4483-b115-42260b0fdb77"),
            tx_coin=order.out_tx_coin,
            tx_to=order.out_tx_to,
        )

        assert eth_out_tx == new_eth_out_tx

        self.txs[bts_in_tx.tx_id] = bts_in_tx
        self.txs[eth_out_tx.tx_id] = eth_out_tx
        self.orders[order.order_id] = Order(
            order_id=order.order_id,
            order_type=order.order_type,
            in_tx=bts_in_tx,
            out_tx=eth_out_tx,
        )

    async def process_database_order(self) -> None:
        if not self.txs or not self.orders:
            return

        in_tx_id = UUID("18f7d676-b20e-4b0b-ba5a-b3617736e938")
        in_order_id = UUID("36aa16d4-e5b3-4c26-8f33-fee982ea02cc")
        out_tx_id = UUID("a4b44708-36bd-4483-b115-42260b0fdb77")
        out_order_id = UUID("ee1af642-d003-435b-8ea9-88b86849bb82")

        if self.step == 0:
            tx_0 = deepcopy(self.txs[in_tx_id])
            tx_0.tx_from = "0xE05c4f7d6e1c774E42B0ca6C833d008467fd361A"
            tx_0.tx_hash = (
                "0xcb164a9f2a66d2f8c564cd5eaaed5a3415cd87af03abcc8278a183eeaceaf38f"
            )
            tx_0.tx_amount = Decimal("50")
            tx_0.tx_created_at = 1594394720
            tx_0.tx_confirmations += 1
            tx_0.tx_max_confirmations = 3

            assert tx_0 == eth_in_tx_0

            self.txs[in_tx_id] = tx_0
            self.orders[in_order_id].in_tx = tx_0
            tx_order = NewInTxOrder(
                order_id=in_order_id,
                tx_hash=tx_0.tx_hash,
                tx_from=tx_0.tx_from,
                tx_amount=tx_0.tx_amount,
                tx_created_at=tx_0.tx_created_at,
                tx_error=tx_0.tx_error,
                tx_confirmations=tx_0.tx_confirmations,
                tx_max_confirmations=tx_0.tx_max_confirmations,
            )

            assert tx_order == new_eth_in_tx_order

            new_tx_order = self.booker.new_in_tx_order(tx_order)

            assert await new_tx_order.asend(None) == None

            with pytest.raises(StopAsyncIteration):
                await new_tx_order.asend(None)
        elif self.step == 1:
            tx_1 = deepcopy(self.txs[in_tx_id])
            tx_1.tx_confirmations += 1

            assert tx_1 == eth_in_tx_1

            self.txs[in_tx_id] = tx_1
            self.orders[in_order_id].in_tx = tx_1
            tx_order = UpdateTxOrder(
                order_id=in_order_id,
                tx_error=tx_1.tx_error,
                tx_confirmations=tx_1.tx_confirmations,
                tx_max_confirmations=tx_1.tx_max_confirmations,
            )

            assert tx_order == update_eth_in_tx_order_0

            update_tx_order = self.booker.update_in_tx_order(tx_order)

            assert await update_tx_order.asend(None) == None

            with pytest.raises(StopAsyncIteration):
                await update_tx_order.asend(None)
        elif self.step == 2:
            tx_2 = deepcopy(self.txs[in_tx_id])
            tx_2.tx_confirmations += 1

            assert tx_2 == eth_in_tx_2

            self.txs[in_tx_id] = tx_2
            self.orders[in_order_id].in_tx = tx_2
            tx_order = UpdateTxOrder(
                order_id=in_order_id,
                tx_error=tx_2.tx_error,
                tx_confirmations=tx_2.tx_confirmations,
                tx_max_confirmations=tx_2.tx_max_confirmations,
            )

            assert tx_order == update_eth_in_tx_order_1

            update_tx_order = self.booker.update_in_tx_order(tx_order)

            assert await update_tx_order.asend(None) == None

            with pytest.raises(StopAsyncIteration):
                await update_tx_order.asend(None)
        elif self.step == 3:
            tx_0 = deepcopy(self.txs[out_tx_id])
            tx_0.tx_from = "0xb6f121Df61ae04D8cb3978BE035C004b24B44283"
            tx_0.tx_hash = (
                "0x684c875217a5a68406aba4cc710f57348c1afe9b27fb244675f987d5e337e019"
            )
            tx_0.tx_amount = Decimal("50")
            tx_0.tx_created_at = 1594403353
            tx_0.tx_confirmations += 1
            tx_0.tx_max_confirmations = 3

            assert tx_0 == eth_out_tx_0

            self.txs[out_tx_id] = tx_0
            self.orders[out_order_id].out_tx = tx_0
            tx_order = NewOutTxOrder(
                order_id=out_order_id,
                tx_hash=tx_0.tx_hash,
                tx_from=tx_0.tx_from,
                tx_amount=tx_0.tx_amount,
                tx_created_at=tx_0.tx_created_at,
                tx_error=tx_0.tx_error,
                tx_confirmations=tx_0.tx_confirmations,
                tx_max_confirmations=tx_0.tx_max_confirmations,
            )

            assert tx_order == new_eth_out_tx_order

            new_tx_order = self.booker.new_out_tx_order(tx_order)

            assert await new_tx_order.asend(None) == None

            with pytest.raises(StopAsyncIteration):
                await new_tx_order.asend(None)
        elif self.step == 4:
            tx_1 = deepcopy(self.txs[out_tx_id])
            tx_1.tx_confirmations += 1

            assert tx_1 == eth_out_tx_1

            self.txs[out_tx_id] = tx_1
            self.orders[out_order_id].out_tx = tx_1
            tx_order = UpdateTxOrder(
                order_id=out_order_id,
                tx_error=tx_1.tx_error,
                tx_confirmations=tx_1.tx_confirmations,
                tx_max_confirmations=tx_1.tx_max_confirmations,
            )

            assert tx_order == update_eth_out_tx_order_0

            update_tx_order = self.booker.update_out_tx_order(tx_order)

            assert await update_tx_order.asend(None) == None

            with pytest.raises(StopAsyncIteration):
                await update_tx_order.asend(None)
        elif self.step == 5:
            tx_2 = deepcopy(self.txs[out_tx_id])
            tx_2.tx_confirmations += 1

            assert tx_2 == eth_out_tx_2

            self.txs[out_tx_id] = tx_2
            self.orders[out_order_id].out_tx = tx_2
            tx_order = UpdateTxOrder(
                order_id=out_order_id,
                tx_error=tx_2.tx_error,
                tx_confirmations=tx_2.tx_confirmations,
                tx_max_confirmations=tx_2.tx_max_confirmations,
            )

            assert tx_order == update_eth_out_tx_order_1

            update_tx_order = self.booker.update_out_tx_order(tx_order)

            assert await update_tx_order.asend(None) == None

            with pytest.raises(StopAsyncIteration):
                await update_tx_order.asend(None)

        self.step += 1

    async def process_orders(self) -> None:
        assert self.step == 0

        while self.step < 6:
            try:
                order = await asyncio.wait_for(self.order_requests.get(), timeout=0.1)
            except asyncio.TimeoutError:
                await self.process_database_order()

                continue

            if isinstance(order, NewInOrder):
                self.process_in_order_request(order)
            elif isinstance(order, NewOutOrder):
                self.process_out_order_request(order)
            else:
                raise ValueError("Unknown order request type")


class MockBTSGatewayBookerOrderAPIClient(AbstractGatewayBookerOrderAPIClient):
    ...


class MockBTSGatewayBookerOrderAPIServer(GatewayBookerOrderAPIServer):
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
        yield ValidatedAddress(valid=True)

    @api_method
    async def get_deposit_address(
        self, args: GetDepositAddress
    ) -> APIStream[DepositAddress, None]:
        if args.out_tx_to is not None:
            raise ValueError("Unknown address")

        yield DepositAddress(tx_to="finteh-usdt")

    @api_method
    async def new_in_order(self, args: NewInOrder) -> APIStream[None, None]:
        await self.order_requests.put(args)

        yield None

    @api_method
    async def new_out_order(self, args: NewOutOrder) -> APIStream[None, None]:
        await self.order_requests.put(args)

        yield None

    def process_in_order_request(self, order: NewInOrder) -> None:
        assert order == new_withdrawal_in_order

        bts_in_tx = Tx(
            tx_id=UUID("387bff73-9d47-4a02-a9b8-20416a4bc212"),
            tx_coin=order.in_tx_coin,
            tx_to=order.in_tx_to,
            tx_amount=order.in_tx_amount,
        )

        assert bts_in_tx == new_bts_in_tx

        eth_out_tx = Tx(
            tx_id=UUID("a4b44708-36bd-4483-b115-42260b0fdb77"),
            tx_coin=order.out_tx_coin,
            tx_to="0x2d6F329Da0e983288E57DBca1e496dd60fae5437",
        )

        assert eth_out_tx == new_eth_out_tx

        eth_out_tx.tx_to = None

        self.txs[bts_in_tx.tx_id] = bts_in_tx
        self.txs[eth_out_tx.tx_id] = eth_out_tx
        self.orders[order.order_id] = Order(
            order_id=order.order_id,
            order_type=order.order_type,
            in_tx=bts_in_tx,
            out_tx=eth_out_tx,
        )

    def process_out_order_request(self, order: NewOutOrder) -> None:
        assert order == new_deposit_out_order

        eth_in_tx = Tx(
            tx_id=UUID("18f7d676-b20e-4b0b-ba5a-b3617736e938"),
            tx_coin=order.in_tx_coin,
            tx_hash=order.in_tx_hash,
            tx_from=order.in_tx_from,
            tx_to=order.in_tx_to,
            tx_amount=order.in_tx_amount,
            tx_created_at=order.in_tx_created_at,
            tx_error=order.in_tx_error,
            tx_confirmations=order.in_tx_confirmations,
            tx_max_confirmations=order.in_tx_max_confirmations,
        )

        assert eth_in_tx == eth_in_tx_2

        bts_out_tx = Tx(
            tx_id=UUID("b78f2cdb-0d8b-479d-8074-9784cb673a0d"),
            tx_coin=order.out_tx_coin,
            tx_to=order.out_tx_to,
        )

        assert bts_out_tx == new_bts_out_tx

        self.txs[eth_in_tx.tx_id] = eth_in_tx
        self.txs[bts_out_tx.tx_id] = bts_out_tx
        self.orders[order.order_id] = Order(
            order_id=order.order_id,
            order_type=order.order_type,
            in_tx=eth_in_tx,
            out_tx=bts_out_tx,
        )

    async def process_database_order(self) -> None:
        if not self.txs or not self.orders:
            return

        out_tx_id = UUID("b78f2cdb-0d8b-479d-8074-9784cb673a0d")
        out_order_id = UUID("36aa16d4-e5b3-4c26-8f33-fee982ea02cc")
        in_tx_id = UUID("387bff73-9d47-4a02-a9b8-20416a4bc212")
        in_order_id = UUID("ee1af642-d003-435b-8ea9-88b86849bb82")

        if self.step == 0:
            tx_0 = deepcopy(self.txs[out_tx_id])
            tx_0.tx_from = "finteh-usdt"
            tx_0.tx_hash = "738bc2bd32e2da31f587d281aa7ee9bd02b9daf0:0"
            tx_0.tx_amount = Decimal("50")
            tx_0.tx_created_at = 1594394731
            tx_0.tx_confirmations += 1
            tx_0.tx_max_confirmations = 3

            assert tx_0 == bts_out_tx_0

            self.txs[out_tx_id] = tx_0
            self.orders[out_order_id].out_tx = tx_0
            tx_order = NewOutTxOrder(
                order_id=out_order_id,
                tx_hash=tx_0.tx_hash,
                tx_from=tx_0.tx_from,
                tx_amount=tx_0.tx_amount,
                tx_created_at=tx_0.tx_created_at,
                tx_error=tx_0.tx_error,
                tx_confirmations=tx_0.tx_confirmations,
                tx_max_confirmations=tx_0.tx_max_confirmations,
            )

            assert tx_order == new_bts_out_tx_order

            new_tx_order = self.booker.new_out_tx_order(tx_order)

            assert await new_tx_order.asend(None) == None

            with pytest.raises(StopAsyncIteration):
                await new_tx_order.asend(None)
        elif self.step == 1:
            tx_1 = deepcopy(self.txs[out_tx_id])
            tx_1.tx_confirmations += 1

            assert tx_1 == bts_out_tx_1

            self.txs[out_tx_id] = tx_1
            self.orders[out_order_id].out_tx = tx_1
            tx_order = UpdateTxOrder(
                order_id=out_order_id,
                tx_error=tx_1.tx_error,
                tx_confirmations=tx_1.tx_confirmations,
                tx_max_confirmations=tx_1.tx_max_confirmations,
            )

            assert tx_order == update_bts_out_tx_order_0

            update_tx_order = self.booker.update_out_tx_order(tx_order)

            assert await update_tx_order.asend(None) == None

            with pytest.raises(StopAsyncIteration):
                await update_tx_order.asend(None)
        elif self.step == 2:
            tx_2 = deepcopy(self.txs[out_tx_id])
            tx_2.tx_confirmations += 1

            assert tx_2 == bts_out_tx_2

            self.txs[out_tx_id] = tx_2
            self.orders[out_order_id].out_tx = tx_2
            tx_order = UpdateTxOrder(
                order_id=out_order_id,
                tx_error=tx_2.tx_error,
                tx_confirmations=tx_2.tx_confirmations,
                tx_max_confirmations=tx_2.tx_max_confirmations,
            )

            assert tx_order == update_bts_out_tx_order_1

            update_tx_order = self.booker.update_out_tx_order(tx_order)

            assert await update_tx_order.asend(None) == None

            with pytest.raises(StopAsyncIteration):
                await update_tx_order.asend(None)
        elif self.step == 3:
            tx_0 = deepcopy(self.txs[in_tx_id])
            tx_0.tx_from = "kwaskoff"
            tx_0.tx_hash = "438bc2bd32e2da76f437d281aa7af9bd02b37af0:0"
            tx_0.tx_amount = Decimal("50")
            tx_0.tx_created_at = 1594403342
            tx_0.tx_confirmations += 1
            tx_0.tx_max_confirmations = 3
            tx_0.memo_to = "0x2d6F329Da0e983288E57DBca1e496dd60fae5437"

            assert tx_0 == bts_in_tx_0

            self.txs[in_tx_id] = tx_0
            self.orders[in_order_id].in_tx = tx_0
            tx_order = NewInTxOrder(
                order_id=in_order_id,
                tx_hash=tx_0.tx_hash,
                tx_from=tx_0.tx_from,
                tx_amount=tx_0.tx_amount,
                tx_created_at=tx_0.tx_created_at,
                tx_error=tx_0.tx_error,
                tx_confirmations=tx_0.tx_confirmations,
                tx_max_confirmations=tx_0.tx_max_confirmations,
                memo_to=tx_0.memo_to,
            )

            assert tx_order == new_bts_in_tx_order

            new_tx_order = self.booker.new_in_tx_order(tx_order)

            assert await new_tx_order.asend(None) == None

            with pytest.raises(StopAsyncIteration):
                await new_tx_order.asend(None)
        elif self.step == 4:
            tx_1 = deepcopy(self.txs[in_tx_id])
            tx_1.tx_confirmations += 1

            assert tx_1 == bts_in_tx_1

            self.txs[in_tx_id] = tx_1
            self.orders[in_order_id].in_tx = tx_1
            tx_order = UpdateTxOrder(
                order_id=in_order_id,
                tx_error=tx_1.tx_error,
                tx_confirmations=tx_1.tx_confirmations,
                tx_max_confirmations=tx_1.tx_max_confirmations,
            )

            assert tx_order == update_bts_in_tx_order_0

            update_tx_order = self.booker.update_in_tx_order(tx_order)

            assert await update_tx_order.asend(None) == None

            with pytest.raises(StopAsyncIteration):
                await update_tx_order.asend(None)
        elif self.step == 5:
            tx_2 = deepcopy(self.txs[in_tx_id])
            tx_2.tx_confirmations += 1

            assert tx_2 == bts_in_tx_2

            self.txs[in_tx_id] = tx_2
            self.orders[in_order_id].in_tx = tx_2
            tx_order = UpdateTxOrder(
                order_id=in_order_id,
                tx_error=tx_2.tx_error,
                tx_confirmations=tx_2.tx_confirmations,
                tx_max_confirmations=tx_2.tx_max_confirmations,
            )

            assert tx_order == update_bts_in_tx_order_1

            update_tx_order = self.booker.update_in_tx_order(tx_order)

            assert await update_tx_order.asend(None) == None

            with pytest.raises(StopAsyncIteration):
                await update_tx_order.asend(None)

        self.step += 1

    async def process_orders(self) -> None:
        assert self.step == 0

        while self.step < 6:
            try:
                order = await asyncio.wait_for(self.order_requests.get(), timeout=0.1)
            except asyncio.TimeoutError:
                await self.process_database_order()

                continue

            if isinstance(order, NewInOrder):
                self.process_in_order_request(order)
            elif isinstance(order, NewOutOrder):
                self.process_out_order_request(order)
            else:
                raise ValueError("Unknown order request type")


def _using_server(
    server: WSJSONRPCAPIsServer,
) -> Callable[[Request], WebSocketResponse]:
    async def handler(request: Request) -> WebSocketResponse:
        stream = WebSocketResponse()

        await stream.prepare(request)

        task = server.add_stream(stream)

        await task

        return stream

    return handler


@pytest.mark.asyncio
async def test_validate_address() -> None:
    apis_server = WSJSONRPCAPIsServer()
    server_task = asyncio.create_task(apis_server.poll())

    app = Application()

    app.add_routes([web.get("/", _using_server(apis_server))])

    server = TestServer(app)

    await server.start_server()

    async def bts_booker_client_ws_stream_constructor() -> ClientWebSocketResponse:
        http_client = TestClient(server)
        client_ws_stream = await http_client.ws_connect("/")

        return client_ws_stream

    bts_booker_apis_client = WSJSONRPCAPIsClient(
        stream_constructor=bts_booker_client_ws_stream_constructor
    )
    bts_booker_client = MockBookerGatewayOrderAPIClient(
        apis_client=bts_booker_apis_client
    )
    bts_server = MockBTSGatewayBookerOrderAPIServer(
        booker=bts_booker_client, order_requests=asyncio.Queue()
    )

    apis_server.api_register(bts_server)

    async def bts_gateway_client_ws_stream_constructor() -> ClientWebSocketResponse:
        http_client = TestClient(server)
        client_ws_stream = await http_client.ws_connect("/")

        return client_ws_stream

    bts_apis_client = WSJSONRPCAPIsClient(
        stream_constructor=bts_gateway_client_ws_stream_constructor
    )
    bts_gateway_client = MockBTSGatewayBookerOrderAPIClient(apis_client=bts_apis_client)

    bts_validate_address = bts_gateway_client.validate_address(
        ValidateAddress(tx_to=new_deposit_in_order.out_tx_to)
    )
    bts_validated_address = await bts_validate_address.asend(None)

    assert bts_validated_address.valid == True

    server_task.cancel()


@pytest.mark.asyncio
async def test_new_out_order() -> None:
    apis_server = WSJSONRPCAPIsServer()
    server_task = asyncio.create_task(apis_server.poll())

    app = Application()

    app.add_routes([web.get("/", _using_server(apis_server))])

    server = TestServer(app)

    await server.start_server()

    async def bts_booker_client_ws_stream_constructor() -> ClientWebSocketResponse:
        http_client = TestClient(server)
        client_ws_stream = await http_client.ws_connect("/")

        return client_ws_stream

    bts_booker_apis_client = WSJSONRPCAPIsClient(
        stream_constructor=bts_booker_client_ws_stream_constructor
    )
    bts_booker_client = MockBookerGatewayOrderAPIClient(
        apis_client=bts_booker_apis_client
    )
    bts_server = MockBTSGatewayBookerOrderAPIServer(
        booker=bts_booker_client, order_requests=asyncio.Queue()
    )

    apis_server.api_register(bts_server)

    async def bts_gateway_client_ws_stream_constructor() -> ClientWebSocketResponse:
        http_client = TestClient(server)
        client_ws_stream = await http_client.ws_connect("/")

        return client_ws_stream

    bts_apis_client = WSJSONRPCAPIsClient(
        stream_constructor=bts_gateway_client_ws_stream_constructor
    )
    bts_gateway_client = MockBTSGatewayBookerOrderAPIClient(apis_client=bts_apis_client)

    new_out_order = bts_gateway_client.new_in_order(new_deposit_out_order)
    processed = await new_out_order.asend(None)
    print(processed)

    server_task.cancel()
