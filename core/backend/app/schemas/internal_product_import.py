from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class ChannelPostProductImport(BaseModel):
    """Body for POST /internal/products/from-channel-post."""
    merchant_id: UUID
    channel_id: int
    primary_message_id: int
    related_message_ids: list[int] = Field(default_factory=list)
    title: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=4000)
    base_price: Decimal | None = Field(default=None, ge=0, decimal_places=2)
    # Image bytes are uploaded separately via /upload-image; we receive URLs.
    image_urls: list[str] = Field(default_factory=list)
