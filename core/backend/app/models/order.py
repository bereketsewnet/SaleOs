from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Index, JSON, Numeric, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.merchant import Merchant


class ChannelSource:
    TELEGRAM = "TELEGRAM"
    TIKTOK = "TIKTOK"
    FACEBOOK = "FACEBOOK"
    INSTAGRAM = "INSTAGRAM"
    WEB_STORE = "WEB_STORE"


class OrderStatus:
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    PAID = "PAID"
    PENDING_MANUAL_REVIEW = "PENDING_MANUAL_REVIEW"
    FULFILLED = "FULFILLED"
    CANCELLED = "CANCELLED"


class Order(Base):
    __tablename__ = "orders"
    __table_args__ = (
        Index("ix_orders_merchant_id", "merchant_id"),
        Index("ix_orders_order_status", "order_status"),
        Index("ix_orders_channel_source", "channel_source"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    merchant_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("merchants.id"), nullable=False
    )
    # Registered SaleOS user (nullable — social buyers are not registered users)
    customer_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    # Anonymous social buyer info e.g. {"telegram_id": 123, "name": "Abebe", "phone": "..."}
    customer_info: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    channel_source: Mapped[str] = mapped_column(String(50), nullable=False)
    channel_order_reference: Mapped[str | None] = mapped_column(String(100), nullable=True)
    total_amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    order_status: Mapped[str] = mapped_column(String(50), default=OrderStatus.PENDING)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    merchant: Mapped[Merchant] = relationship("Merchant", back_populates="orders")
    items: Mapped[list[OrderItem]] = relationship("OrderItem", back_populates="order")


class OrderItem(Base):
    __tablename__ = "order_items"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    order_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("orders.id"), nullable=False
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("products.id"), nullable=False
    )
    quantity: Mapped[int] = mapped_column(nullable=False)
    unit_price: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    order: Mapped[Order] = relationship("Order", back_populates="items")
