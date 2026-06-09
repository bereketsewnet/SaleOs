from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.product import Product
    from app.models.order import Order
    from app.models.payment_account import MerchantPaymentAccount


class Merchant(Base, TimestampMixin):
    __tablename__ = "merchants"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    business_name: Mapped[str] = mapped_column(String(255), nullable=False)
    contact_phone: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)
    contact_email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    users: Mapped[list[User]] = relationship("User", back_populates="merchant")
    products: Mapped[list[Product]] = relationship("Product", back_populates="merchant")
    orders: Mapped[list[Order]] = relationship("Order", back_populates="merchant")
    payment_accounts: Mapped[list[MerchantPaymentAccount]] = relationship(
        "MerchantPaymentAccount", back_populates="merchant"
    )
