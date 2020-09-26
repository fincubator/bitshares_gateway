from typing import ClassVar, Type
from decimal import Decimal
from uuid import UUID
from enum import Enum
import dataclasses

from marshmallow import Schema as MarshmallowSchema, fields
from marshmallow_dataclass import dataclass, NewType as MarshmallowNewType
from booker.finteh_proto.dto import (
    DataTransferClass,
    dataclass,
    Amount,
    TransactionDTO,
    OrderDTO,
)


class DTOInvalidType(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)


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
    UNKNOWN_ERROR = 1
    BAD_ASSET = 2
    LESS_MIN = 3
    GREATER_MAX = 4
    NO_MEMO = 5
    FLOOD_MEMO = 6
    OP_COLLISION = 7
    TX_HASH_NOT_FOUND = 8


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

    memo: str = None


def op_to_order(op_dto: BitSharesOperation):
    BITSHARES_NEED_CONF = 5  # TODO replace with context

    tx = TransactionDTO(
        coin=op_dto.asset,
        amount=op_dto.amount,
        from_address=op_dto.from_account,
        to_address=op_dto.to_account,
        created_at=op_dto.tx_created_at,
        confirmations=op_dto.confirmations,
        max_confirmations=BITSHARES_NEED_CONF,
        error=op_dto.error,
        tx_id=f"{op_dto.op_id}:{op_dto.tx_hash}",
    )

    if op_dto.order_type == OrderType.DEPOSIT:
        in_tx = None
        out_tx = tx
    elif op_dto.order_type == OrderType.DEPOSIT:
        in_tx = tx
        out_tx = None
    else:
        raise

    order_dto = OrderDTO(
        op_id=op_dto.op_id, order_type=op_dto.order_type, in_tx=in_tx, out_tx=out_tx
    )
