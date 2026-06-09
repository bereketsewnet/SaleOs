from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class MerchantCreate(BaseModel):
    business_name: str = Field(min_length=2, max_length=200)
    contact_phone: str = Field(min_length=7, max_length=20)
    contact_email: EmailStr


class MerchantPublic(BaseModel):
    id: UUID
    business_name: str
    contact_phone: str
    contact_email: EmailStr
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}
