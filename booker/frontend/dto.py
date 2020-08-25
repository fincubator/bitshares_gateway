from typing import Optional
from uuid import UUID

from marshmallow_dataclass import dataclass

from booker.dto import DataTransferClass, Amount
from booker.gateway.dto import OrderType, TxError


@dataclass
class NewInOrder(DataTransferClass):
    """Create a new inbound order.
    """

    in_tx_coin: str
    in_tx_amount: Amount
    out_tx_coin: str
    out_tx_to: Optional[str] = None


@dataclass
class InOrder(DataTransferClass):
    """Created a new inbound order.
    """

    order_id: UUID
    in_tx_to: str


@dataclass
class Order(DataTransferClass):
    order_type: OrderType
    in_tx_coin: str
    in_tx_hash: Optional[str]
    """
    A transaction identifier, simple or composite, consisting of a transaction
    identifier and an index, for example, 'txid:output_index'.
    """
    in_tx_from: Optional[str]
    in_tx_to: Optional[str]
    in_tx_amount: Amount
    in_tx_created_at: int
    in_tx_error: TxError
    in_tx_confirmations: int
    in_tx_max_confirmations: int
    out_tx_coin: str
    out_tx_hash: Optional[str]
    """
    A transaction identifier, simple or composite, consisting of a transaction
    identifier and an index, for example, 'txid:output_index'.
    """
    out_tx_from: Optional[str]
    out_tx_to: Optional[str]
    out_tx_amount: Amount
    out_tx_created_at: int
    out_tx_error: TxError
    out_tx_confirmations: int
    out_tx_max_confirmations: int
