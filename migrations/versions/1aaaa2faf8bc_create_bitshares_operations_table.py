"""Create bitshares operations table

Revision ID: 1aaaa2faf8bc
Revises: 8cfdcd120d14
Create Date: 2020-06-30 01:38:41.049590

"""
import sys

sys.path.append("/app")

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

import datetime


# revision identifiers, used by Alembic.
revision = "1aaaa2faf8bc"
down_revision = "8cfdcd120d14"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "bitshares_operations",
        sa.Column("pk", sa.Integer, primary_key=True, index=True),
        sa.Column("op_id", sa.Integer, unique=True),
        sa.Column("order_id", UUID(as_uuid=True), unique=True),
        sa.Column("order_type", sa.Integer),
        sa.Column("asset", sa.String),
        sa.Column("from_account", sa.String),
        sa.Column("to_account", sa.String),
        sa.Column("amount", sa.Numeric),
        sa.Column("status", sa.String),
        sa.Column("confirmations", sa.Integer),
        sa.Column("block_num", sa.String),
        sa.Column("tx_hash", sa.String),
        sa.Column("tx_created_at", sa.DateTime, default=datetime.datetime.utcnow()),
        sa.Column("tx_expiration", sa.DateTime),
        sa.Column("error", sa.Integer),
    )


def downgrade():
    op.drop_table("bitshares_operations")
