from typing import ClassVar, Type
from decimal import Decimal
from uuid import UUID
from enum import Enum

from marshmallow import Schema as MarshmallowSchema, fields
from marshmallow_dataclass import dataclass, NewType as MarshmallowNewType


class DTOInvalidType(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)


@dataclass
class DataTransferClass:
    Schema: ClassVar[Type[MarshmallowSchema]] = MarshmallowSchema


def AmountField(*args, **kwargs):
    return fields.Decimal(*args, **kwargs, as_string=True)


Amount = MarshmallowNewType("Amount", Decimal, field=AmountField)


class OrderType(Enum):
    TRASH = 0
    DEPOSIT = 1
    WITHDRAWAL = 2


class TxStatus(Enum):
    ERROR = 0
    WAIT = 1
    RECEIVED_NOT_CONFIRMED = 2
    RECEIVED_AND_CONFIRMED = 3


class TxError(Enum):
    NO_ERROR = 0
    BAD_ASSET = 1
    LESS_MIN = 2
    GREATER_MAX = 3
    NO_MEMO = 4
    FLOOD_MEMO = 5


@dataclass
class BitSharesOperation(DataTransferClass):
    op_id: int = None

    order_id: UUID = None
    order_type: OrderType = None

    asset: str = None
    from_account: str = None
    to_account: str = None
    amount: Amount = None

    status: TxStatus = None
    confirmations: int = None
    block_num: int = None

    tx_hash: str = None
    tx_created_at: int = None
    tx_expiration: int = None

    error: TxError = None

    def as_model(self):
        from db_utils.models import BitsharesOperation as Model

        return Model(**self.__dict__)
