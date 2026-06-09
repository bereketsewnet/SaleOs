"""telegram_bot_configs.business_mode

Revision ID: c8f44d9b1ea3
Revises: b7d22a91c4f0
Create Date: 2026-06-09 22:50:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c8f44d9b1ea3"
down_revision: Union[str, None] = "b7d22a91c4f0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "telegram_bot_configs",
        sa.Column(
            "business_mode",
            sa.String(length=30),
            nullable=False,
            server_default="PRODUCT_SALES",
        ),
    )


def downgrade() -> None:
    op.drop_column("telegram_bot_configs", "business_mode")
