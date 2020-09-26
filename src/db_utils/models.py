import datetime

import sqlalchemy as sa
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import UUID

# from migrations import metadata
from src.gw_dto import TxStatus, TxError, OrderType

Base = declarative_base()


class GatewayWallet(Base):
    __tablename__ = "gateway_wallets"

    pk = sa.Column(sa.Integer, primary_key=True, index=True)

    account_name = sa.Column(sa.String, unique=True)
    last_parsed_block = sa.Column(sa.Integer)
    last_operation = sa.Column(sa.Integer)


class BitsharesOperation(Base):
    __tablename__ = "bitshares_operations"

    pk = sa.Column(sa.Integer, primary_key=True, index=True)

    op_id = sa.Column(sa.Integer, unique=True)
    order_id = sa.Column(UUID(as_uuid=True), unique=True)
    order_type = sa.Column(sa.Enum(OrderType))

    asset = sa.Column(sa.String)
    from_account = sa.Column(sa.String)
    to_account = sa.Column(sa.String)
    amount = sa.Column(sa.Numeric)

    status = sa.Column(sa.Enum(TxStatus))
    confirmations = sa.Column(sa.Integer)
    block_num = sa.Column(sa.Integer)

    tx_hash = sa.Column(sa.String)
    tx_created_at = sa.Column(sa.DateTime, default=datetime.datetime.utcnow())
    tx_expiration = sa.Column(sa.DateTime)

    error = sa.Column(sa.Enum(TxError))

    memo = sa.Column(sa.String)
