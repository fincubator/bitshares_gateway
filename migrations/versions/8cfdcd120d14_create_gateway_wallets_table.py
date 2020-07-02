"""Create gateway_accounts table

Revision ID: 8cfdcd120d14
Revises:
Create Date: 2020-06-12 19:03:34.527235

"""
import sys

sys.path.append("/app")

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "8cfdcd120d14"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "gateway_wallets",
        sa.Column("pk", sa.Integer, primary_key=True, index=True),
        sa.Column("account_name", sa.String, unique=True),
        sa.Column("last_parsed_block", sa.Integer),
        sa.Column("last_operation", sa.Integer),
    )


def downgrade():
    op.drop_table("gateway_wallets")
