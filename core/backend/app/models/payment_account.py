from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin

if TYPE_CHECKING:
    from app.models.merchant import Merchant


class MerchantPaymentAccount(Base, TimestampMixin):
    """
    Bank accounts merchants configure for Phase 1 manual payment flow.
    Displayed to customers when OCR is not yet available.
    Used by all channel microservices (Telegram, Instagram, Facebook).
    """
    __tablename__ = "merchant_payment_accounts"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    merchant_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("merchants.id"), nullable=False
    )
    bank_name: Mapped[str] = mapped_column(String(100), nullable=False)
    account_number: Mapped[str] = mapped_column(String(50), nullable=False)
    account_holder_name: Mapped[str] = mapped_column(String(150), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    merchant: Mapped[Merchant] = relationship("Merchant", back_populates="payment_accounts")
