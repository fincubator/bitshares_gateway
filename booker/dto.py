from __future__ import annotations
from typing import ClassVar, Type
import dataclasses
from decimal import Decimal

import marshmallow
from marshmallow import Schema as MarshmallowSchema
from marshmallow_dataclass import dataclass, NewType as MarshmallowNewType


class DTOInvalidType(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)


@dataclass
class DataTransferClass:
    Schema: ClassVar[Type[MarshmallowSchema]] = MarshmallowSchema


    def update(self, dto: DataTransferClass) -> None:
        dto_dict = dataclasses.asdict(dto)

        for key, value in dto_dict.items():
            if value is not None:
                setattr(self, key, value)


def AmountField(*args, **kwargs):
    return marshmallow.fields.Decimal(*args, **kwargs, as_string=True)


Amount = MarshmallowNewType("Amount", Decimal, field=AmountField)
