import pytest

from db_utils.models import BitsharesOperation as BitSharesOperationModel, GatewayWallet
from dto import BitSharesOperation as BitSharesOperationDTO


def test_bitshares_operation():
    op_data = {"op_id": 666}
    op_dto = BitSharesOperationDTO(**op_data)
    op_model = BitSharesOperationModel(**op_dto.__dict__)
    assert op_dto.op_id == op_model.op_id == op_data["op_id"]


def test_gateway_wallet():
    pass
