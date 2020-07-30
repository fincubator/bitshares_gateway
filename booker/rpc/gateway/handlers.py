from booker.app import AppContext
from booker.rpc.api import APIStream, api_method
from booker.gateway.dto import (
    NewInOrderRequest,
    NewInTxOrder,
    NewOutTxOrder,
    UpdateTxOrder,
)
from booker.rpc.gateway.api import AbstractBookerGatewayOrderAPIServer
from booker.gateway.api import (
    new_in_order_request,
    new_in_tx_order,
    update_in_tx_order,
    new_out_tx_order,
    update_out_tx_order,
)


class BookerGatewayOrderAPIServer(AbstractBookerGatewayOrderAPIServer):
    context: AppContext

    def __init__(self, context: AppContext) -> None:
        super().__init__()

        self.context = context

    @api_method
    async def new_in_order_request(
        self, args: NewInOrderRequest
    ) -> APIStream[None, None]:
        yield await new_in_order_request(self.context, args)

    @api_method
    async def new_in_tx_order(self, args: NewInTxOrder) -> APIStream[None, None]:
        yield await new_in_tx_order(self.context, args)

    @api_method
    async def new_in_tx_order(self, args: NewInTxOrder) -> APIStream[None, None]:
        yield await new_in_tx_order(self.context, args)

    @api_method
    async def update_in_tx_order(self, args: UpdateTxOrder) -> APIStream[None, None]:
        yield await update_in_tx_order(self.context, args)

    @api_method
    async def new_out_tx_order(self, args: NewOutTxOrder) -> APIStream[None, None]:
        yield await new_out_tx_order(self.context, args)

    @api_method
    async def update_out_tx_order(self, args: UpdateTxOrder) -> APIStream[None, None]:
        yield await update_out_tx_order(self.context, args)
