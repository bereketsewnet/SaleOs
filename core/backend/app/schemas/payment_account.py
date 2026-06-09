from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class PaymentAccountBase(BaseModel):
    bank_name: str = Field(min_length=1, max_length=100)
    account_number: str = Field(min_length=1, max_length=50)
    account_holder_name: str = Field(min_length=1, max_length=150)
    phone: str | None = Field(default=None, max_length=20)


class PaymentAccountCreate(PaymentAccountBase):
    pass


class PaymentAccountUpdate(BaseModel):
    bank_name: str | None = Field(default=None, min_length=1, max_length=100)
    account_number: str | None = Field(default=None, min_length=1, max_length=50)
    account_holder_name: str | None = Field(default=None, min_length=1, max_length=150)
    phone: str | None = Field(default=None, max_length=20)
    is_active: bool | None = None


class PaymentAccountPublic(PaymentAccountBase):
    id: UUID
    merchant_id: UUID
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}
