from typing import Optional
from uuid import UUID
from enum import Enum

from marshmallow_dataclass import dataclass

from booker.dto import DataTransferClass, Amount


class OrderType(Enum):
    TRASH = 0
    DEPOSIT = 1
    WITHDRAWAL = 2


class TxError(Enum):
    NO_ERROR = 0
    UNKNOWN_ERROR = 1


@dataclass
class ValidateAddress(DataTransferClass):
    tx_to: str


@dataclass
class ValidatedAddress(DataTransferClass):
    valid: bool


@dataclass
class GetDepositAddress(DataTransferClass):
    out_tx_to: Optional[str] = None


@dataclass
class DepositAddress(DataTransferClass):
    tx_to: str


@dataclass
class NewInOrder(DataTransferClass):
    """Create a new inbound order with order_id identifier.
    """

    order_id: UUID
    order_type: OrderType
    in_tx_coin: str
    in_tx_to: str
    in_tx_amount: Amount
    out_tx_coin: str
    out_tx_to: Optional[str] = None


@dataclass
class NewOutOrder(DataTransferClass):
    """Create a new outbound order with order_id identifier.
    """

    order_id: UUID
    order_type: OrderType
    in_tx_coin: str
    in_tx_hash: str
    """
    A transaction identifier, simple or composite, consisting of a transaction
    identifier and an index, for example, 'txid:output_index'.
    """
    in_tx_from: str
    in_tx_to: str
    in_tx_amount: Amount
    in_tx_created_at: int
    in_tx_error: TxError
    in_tx_confirmations: int
    in_tx_max_confirmations: int
    out_tx_coin: str
    out_tx_to: str


@dataclass
class NewInOrderRequest(DataTransferClass):
    """Create a request to create new inbound order without order_id identifier.
    """

    order_type: OrderType
    in_tx_coin: str
    in_tx_to: str
    in_tx_amount: Amount
    out_tx_coin: str
    out_tx_to: str


@dataclass
class NewInTxOrder(DataTransferClass):
    """Creates a new inbound transaction in the Booker database and binds it to
    the order with the order_id identifier.
    """

    order_id: UUID
    tx_hash: str
    """A transaction identifier, simple or composite, consisting of a
    transaction identifier and an index, for example, 'txid:output_index'.
    """
    tx_from: str
    tx_amount: Amount
    tx_created_at: int
    tx_error: TxError
    tx_confirmations: int
    tx_max_confirmations: int
    memo_to: Optional[str] = None


@dataclass
class NewOutTxOrder(DataTransferClass):
    """
    Creates a new outbound transaction in the Booker database and binds it to
    the order with the order_id identifier.
    """

    order_id: UUID
    tx_hash: str
    """A transaction identifier, simple or composite, consisting of a
    transaction identifier and an index, for example, 'txid:output_index'.
    """
    tx_from: str
    tx_amount: Amount
    tx_created_at: int
    tx_error: TxError
    tx_confirmations: int
    tx_max_confirmations: int


@dataclass
class UpdateTxOrder(DataTransferClass):
    """Updates a transaction in the Booker database that is bound to the order
    with the order_id identifier.
    """

    order_id: UUID
    tx_error: TxError
    tx_confirmations: int
    tx_max_confirmations: int
