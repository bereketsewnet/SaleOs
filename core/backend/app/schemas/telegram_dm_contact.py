from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

DMContactKind = Literal[
    "TELEGRAM_USERNAME",
    "PHONE",
    "EMAIL",
    "ADDRESS",
    "OTHER",
]


class DMContactCreate(BaseModel):
    kind: DMContactKind
    value: str = Field(min_length=1, max_length=255)
    label: str | None = Field(default=None, max_length=80)
    position: int = Field(default=0, ge=0)
    is_active: bool = True


class DMContactUpdate(BaseModel):
    kind: DMContactKind | None = None
    value: str | None = Field(default=None, min_length=1, max_length=255)
    label: str | None = Field(default=None, max_length=80)
    position: int | None = Field(default=None, ge=0)
    is_active: bool | None = None


class DMContactPublic(BaseModel):
    id: UUID
    merchant_id: UUID
    kind: DMContactKind
    value: str
    label: str | None
    position: int
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class DMContactReorderItem(BaseModel):
    id: UUID
    position: int = Field(ge=0)
