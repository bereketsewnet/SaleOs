from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class ProductCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=4000)
    base_price: Decimal | None = Field(default=None, ge=0, decimal_places=2)
    sku: str | None = Field(default=None, max_length=100)
    image_urls: list[str] = Field(default_factory=list)
    initial_stock: int = Field(default=0, ge=0)
    publish_to_channel: bool = False
    # Per-product AI context (private — never in channel caption)
    identifier: str | None = Field(default=None, max_length=4000)
    instructions: str | None = Field(default=None, max_length=4000)
    # If true, after create kick off OCR vision to auto-fill identifier from images.
    run_ocr: bool = False


class ProductUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=4000)
    base_price: Decimal | None = Field(default=None, ge=0, decimal_places=2)
    sku: str | None = Field(default=None, max_length=100)
    image_urls: list[str] | None = None
    identifier: str | None = Field(default=None, max_length=4000)
    instructions: str | None = Field(default=None, max_length=4000)


class ProductPublic(BaseModel):
    id: UUID
    merchant_id: UUID
    title: str
    description: str | None
    base_price: Decimal | None
    sku: str | None
    image_urls: list[str]
    quantity: int = 0
    reserved_quantity: int = 0
    is_published_to_channel: bool = False
    identifier: str | None = None
    instructions: str | None = None
    is_ocr_identified: bool = False
    created_at: datetime

    model_config = {"from_attributes": True}


class UploadedImage(BaseModel):
    url: str
    bucket: str
    object_key: str


class StockAdjust(BaseModel):
    delta: int = Field(..., description="Positive to add stock, negative to remove.")
    reason: str | None = Field(default=None, max_length=200)


class ProductAgentContext(BaseModel):
    """Returned by the internal endpoint the Telegram svc calls before replying.
    Effective values: per-product if set, else default from telegram_bot_configs."""
    product_id: UUID
    merchant_id: UUID
    title: str
    description: str | None
    base_price: Decimal | None
    image_urls: list[str]
    identifier_effective: str | None
    instructions_effective: str | None
    is_ocr_identified: bool


class OCRResult(BaseModel):
    """Internal — Telegram svc PATCHes this back after running vision."""
    identifier: str = Field(min_length=1, max_length=4000)
