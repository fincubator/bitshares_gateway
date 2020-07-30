from abc import ABC, abstractmethod

from booker.rpc.api import APIStream, api_method, api_client, api_server
from booker.gateway.dto import (
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


class AbstractBookerGatewayOrderAPI(ABC):
    @api_method
    @abstractmethod
    async def new_in_order_request(
        self, args: NewInOrderRequest
    ) -> APIStream[None, None]:
        """Create a request to create new inbound order without order_id
        identifier.
        """
        yield None

    @api_method
    @abstractmethod
    async def new_in_tx_order(self, args: NewInTxOrder) -> APIStream[None, None]:
        """Creates a new inbound transaction in the Booker database and binds it
        to the order with the order_id identifier.
        """
        yield None

    @api_method
    @abstractmethod
    async def update_in_tx_order(self, args: UpdateTxOrder) -> APIStream[None, None]:
        """Updates a inbound transaction in the Booker database that is bound to
        the order with the order_id identifier.
        """
        yield None

    @api_method
    @abstractmethod
    async def new_out_tx_order(self, args: NewOutTxOrder) -> APIStream[None, None]:
        """Creates a new outbound transaction in the Booker database and binds
        it to the order with the order_id identifier.
        """
        yield None

    @api_method
    @abstractmethod
    async def update_out_tx_order(self, args: UpdateTxOrder) -> APIStream[None, None]:
        """Updates a outbound transaction in the Booker database that is bound
        to the order with the order_id identifier.
        """
        yield None


@api_server
class AbstractBookerGatewayOrderAPIServer(AbstractBookerGatewayOrderAPI):
    ...


class AbstractGatewayBookerOrderAPI(ABC):
    @api_method
    @abstractmethod
    async def validate_address(
        self, args: ValidateAddress
    ) -> APIStream[ValidatedAddress, None]:
        yield None

    @api_method
    @abstractmethod
    async def get_deposit_address(
        self, args: GetDepositAddress
    ) -> APIStream[DepositAddress, None]:
        yield None

    @api_method
    @abstractmethod
    async def new_in_order(self, args: NewInOrder) -> APIStream[None, None]:
        """Create a new inbound order with order_id identifier.
        """
        yield None

    @api_method
    @abstractmethod
    async def new_out_order(self, args: NewOutOrder) -> APIStream[None, None]:
        """Create a new outbound order with order_id identifier.
        """
        yield None


@api_client
class AbstractGatewayBookerOrderAPIClient(AbstractGatewayBookerOrderAPI):
    ...
