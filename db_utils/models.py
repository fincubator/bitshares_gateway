import uuid
import datetime

import sqlalchemy as sa
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import UUID
# from migrations import metadata

from config import sql_conn_url

Base = declarative_base()

# not-async engine for using in migrations
engine = create_engine(sql_conn_url, echo=False)


def create_all():
    Base.metadata.create_all(engine)


class GatewayAccount(Base):
    __tablename__ = "gateway_accounts"

    pk = sa.Column(sa.Integer, primary_key=True, index=True)

    account_name = sa.Column(sa.String, unique=True)
    last_parsed_block = sa.Column(sa.Integer)
    last_operation = sa.Column(sa.Integer)


class Order(Base):
    __tablename__ = "orders"

    pk = sa.Column(sa.Integer, primary_key=True, index=True)
    order_uuid = sa.Column(UUID(as_uuid=True), unique=True)
    order_type = sa.Column(sa.Integer)
    # user = ... # TODO foreign_key Users.id
    completed = sa.Column(sa.Boolean)

    in_tx_coin = sa.Column(sa.String)
    in_tx_to = sa.Column(sa.String)
    in_tx_from = sa.Column(sa.String)
    in_tx_hash = sa.Column(sa.String, unique=True)
    in_tx_amount = sa.Column(sa.Numeric)
    in_tx_status = sa.Column(sa.Integer)
    in_tx_confirmations = sa.Column(sa.Integer)
    in_tx_created_at = sa.Column(sa.DateTime, default=datetime.datetime.utcnow())
    in_tx_error = sa.Column(sa.Integer, default=0)

    out_tx_coin = sa.Column(sa.String)
    out_tx_to = sa.Column(sa.String)
    out_tx_from = sa.Column(sa.String)
    out_tx_hash = sa.Column(sa.String, unique=True)
    out_tx_amount = sa.Column(sa.Numeric)
    out_tx_status = sa.Column(sa.Integer)
    out_tx_confirmations = sa.Column(sa.Integer)
    out_tx_created_at = sa.Column(sa.DateTime, default=datetime.datetime.utcnow())
    out_tx_error = sa.Column(sa.Integer, default=0)


class BitsharesOperation(Base):
    __tablename__ = "bitshares_operations"

    pk = sa.Column(sa.Integer, primary_key=True, index=True)
    op_id = sa.Column(sa.Integer, unique=True)
    # order = ... # ???
    op_type = sa.Column(sa.Integer)

    broadcaster_account = sa.Column(sa.String)
    target_account = sa.Column(sa.String)
    amount = sa.Column(sa.Numeric)
    asset = sa.Column(sa.String)

    status = sa.Column(sa.Integer)
    confirmations = sa.Column(sa.Integer)
    block_num = sa.Column(sa.Integer)
    created_at = sa.Column(sa.DateTime, default=datetime.datetime.utcnow())
    expiration = sa.Column(sa.DateTime, default=datetime.datetime.utcnow())

    fee_asset = sa.Column(sa.String)
    fee_amount = sa.Column(sa.Numeric)
