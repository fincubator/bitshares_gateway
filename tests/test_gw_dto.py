import pytest

from src.gw_dto import Amount, BitSharesOperation


def test_amount():
    value = 0.111111111111111111111111112
    amount = Amount(value)
    assert value - amount == 0.0
