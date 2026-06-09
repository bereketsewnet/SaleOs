"""order payment proof + v2 status enum

Revision ID: b7d22a91c4f0
Revises: f03b51db6828
Create Date: 2026-06-09 21:00:00.000000

Adds payment-receipt columns to orders and remaps the order_status string
values to the new 8-state payment-first flow.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b7d22a91c4f0"
down_revision: Union[str, None] = "f03b51db6828"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


_FORWARD_STATUS_MAP = {
    "PENDING": "PENDING_PAYMENT",
    "PROCESSING": "PREPARING",
    "PAID": "PAYMENT_VERIFIED",
    "PENDING_MANUAL_REVIEW": "PAYMENT_SUBMITTED",
    "FULFILLED": "DELIVERED",
    "CANCELLED": "CANCELLED",
}

_BACKWARD_STATUS_MAP = {
    "PENDING_PAYMENT": "PENDING",
    "PAYMENT_SUBMITTED": "PENDING_MANUAL_REVIEW",
    "PAYMENT_VERIFIED": "PAID",
    "PAYMENT_REJECTED": "PENDING_MANUAL_REVIEW",
    "PREPARING": "PROCESSING",
    "SHIPPED": "PROCESSING",
    "DELIVERED": "FULFILLED",
    "CANCELLED": "CANCELLED",
}


def upgrade() -> None:
    op.add_column("orders", sa.Column("payment_proof_url", sa.Text(), nullable=True))
    op.add_column(
        "orders",
        sa.Column("payment_proof_uploaded_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "orders",
        sa.Column("payment_verified_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column("orders", sa.Column("payment_verified_by", sa.Uuid(), nullable=True))
    op.add_column(
        "orders", sa.Column("payment_rejection_reason", sa.Text(), nullable=True)
    )
    op.create_foreign_key(
        "fk_orders_payment_verified_by_users",
        "orders",
        "users",
        ["payment_verified_by"],
        ["id"],
        ondelete="SET NULL",
    )

    bind = op.get_bind()
    for old, new in _FORWARD_STATUS_MAP.items():
        bind.execute(
            sa.text("UPDATE orders SET order_status = :new WHERE order_status = :old"),
            {"new": new, "old": old},
        )


def downgrade() -> None:
    bind = op.get_bind()
    for new, old in _BACKWARD_STATUS_MAP.items():
        bind.execute(
            sa.text("UPDATE orders SET order_status = :old WHERE order_status = :new"),
            {"new": new, "old": old},
        )
    op.drop_constraint(
        "fk_orders_payment_verified_by_users", "orders", type_="foreignkey"
    )
    op.drop_column("orders", "payment_rejection_reason")
    op.drop_column("orders", "payment_verified_by")
    op.drop_column("orders", "payment_verified_at")
    op.drop_column("orders", "payment_proof_uploaded_at")
    op.drop_column("orders", "payment_proof_url")
