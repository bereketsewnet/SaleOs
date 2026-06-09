from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey, Integer, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.product import Product


class InventoryLedger(Base):
    __tablename__ = "inventory_ledger"
    __table_args__ = (
        CheckConstraint("quantity >= 0", name="ck_quantity_non_negative"),
        CheckConstraint("reserved_quantity >= 0", name="ck_reserved_non_negative"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("products.id"), unique=True, nullable=False
    )
    merchant_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("merchants.id"), nullable=False
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    reserved_quantity: Mapped[int] = mapped_column(Integer, default=0)
    location_label: Mapped[str] = mapped_column(String(100), default="Central Warehouse")

    product: Mapped[Product] = relationship("Product", back_populates="inventory")
