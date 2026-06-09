from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import (
    ARRAY,
    Boolean,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin

if TYPE_CHECKING:
    from app.models.merchant import Merchant
    from app.models.inventory import InventoryLedger


class Product(Base, TimestampMixin):
    __tablename__ = "products"
    __table_args__ = (
        UniqueConstraint("merchant_id", "sku", name="uq_merchant_sku"),
        Index("ix_products_merchant_id", "merchant_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    merchant_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("merchants.id"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Price + SKU are optional — auto-generated SKU if missing.
    base_price: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    sku: Mapped[str | None] = mapped_column(String(100), nullable=True)
    image_urls: Mapped[list[str]] = mapped_column(ARRAY(Text), server_default="{}")
    # True once the product has been posted to the Telegram channel.
    # Set False again on any product edit so the merchant can re-publish updates.
    is_published_to_channel: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="false", default=False
    )
    # Per-product AI context. Private — never shown to customers in the channel caption.
    # identifier: rich description for the agent (color, variant, stock note, multi-language OK).
    # instructions: per-product reply rules the agent must follow strictly.
    identifier: Mapped[str | None] = mapped_column(Text, nullable=True)
    instructions: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_ocr_identified: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="false", default=False
    )

    merchant: Mapped[Merchant] = relationship("Merchant", back_populates="products")
    inventory: Mapped[InventoryLedger | None] = relationship(
        "InventoryLedger", back_populates="product", uselist=False
    )
