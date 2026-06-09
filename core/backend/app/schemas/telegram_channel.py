from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class TelegramChannelStatus(BaseModel):
    """Returned to admin panel to show connection state."""
    connected: bool
    channel_id: int | None = None
    channel_username: str | None = None
    channel_title: str | None = None


class TelegramChannelBind(BaseModel):
    """Internal — payload from Telegram svc when bot is promoted as channel admin."""
    channel_id: int
    channel_username: str | None = None
    channel_title: str | None = None


class TelegramChannelPostPublic(BaseModel):
    id: UUID
    channel_id: int
    message_id: int
    caption: str | None
    photo_file_id: str | None
    posted_by_admin: bool
    product_id: UUID | None
    posted_at: datetime

    model_config = {"from_attributes": True}


class TelegramChannelPostIngest(BaseModel):
    """Internal — passive ingest (channel_post handler) or active publish ingest.

    Race-safe upsert: if a row exists with the same (channel_id, message_id),
    posted_by_admin and product_id are promoted only when provided here.
    """
    channel_id: int
    message_id: int = Field(..., gt=0)
    caption: str | None = Field(default=None, max_length=4096)
    photo_file_id: str | None = Field(default=None, max_length=255)
    posted_by_admin: bool = False
    product_id: UUID | None = None
