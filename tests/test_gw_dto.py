import pytest
from uuid import uuid4
from src.gw_dto import Amount, BitSharesOperation, OrderType, TxStatus, TxError
from booker.finteh_proto.dto import OrderDTO, TransactionDTO
from src.config import Config, BITSHARES_NEED_CONF
from tests.fixtures import *
import datetime


def test_amount():
    value = 0.111111111111111111111111112
    amount = Amount(value)
    assert value - amount == 0.0


def test_op_to_order():
    cfg = Config()
    op_dto = BitSharesOperation(
        op_id=43571314,
        order_id=uuid4(),
        order_type=OrderType.DEPOSIT,
        asset=f"{cfg.gateway_prefix}.{cfg.gateway_distribute_asset}",
        from_account=cfg.account,
        to_account=testnet_user_account,
        amount=0.1,
        status=TxStatus.RECEIVED_NOT_CONFIRMED,
        confirmations=0,
        block_num=37899972,
        tx_created_at=datetime.datetime.now(),
        error=TxError.NO_ERROR,
    )

    tx = TransactionDTO(
        coin=op_dto.asset,
        amount=op_dto.amount,
        from_address=op_dto.from_account,
        to_address=op_dto.to_account,
        created_at=op_dto.tx_created_at,
        confirmations=op_dto.confirmations,
        max_confirmations=BITSHARES_NEED_CONF,
    )
