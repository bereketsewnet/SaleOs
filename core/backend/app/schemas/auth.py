from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    business_name: str = Field(min_length=2, max_length=200)
    contact_phone: str = Field(min_length=7, max_length=20)
    contact_email: EmailStr
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserPublic(BaseModel):
    id: UUID
    email: EmailStr
    first_name: str
    last_name: str
    phone_number: str | None = None
    role: str
    merchant_id: UUID | None = None
    is_verified: bool
    created_at: datetime

    model_config = {"from_attributes": True}
