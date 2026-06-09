from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

LanguagePref = Literal["AMHARIC", "ENGLISH", "AUTO"]
BusinessMode = Literal["PRODUCT_SALES", "SERVICE_INQUIRY"]


class TelegramBotConfigUpsert(BaseModel):
    """Connection-related fields: token + language + welcome.
    Brand voice is updated separately via TelegramBrandVoiceUpdate."""
    bot_token: str = Field(min_length=20, max_length=255)
    language_preference: LanguagePref = "AUTO"
    welcome_message: str | None = Field(default=None, max_length=2000)


class TelegramBrandVoiceUpdate(BaseModel):
    """Telegram-specific brand voice. Other platforms have their own."""
    business_type: str | None = Field(default=None, max_length=100)
    business_description: str | None = Field(default=None, max_length=2000)
    system_prompt: str | None = Field(default=None, max_length=8000)
    business_mode: BusinessMode | None = None
    # Defaults inherited by every product (used when product.identifier/instructions are blank)
    default_product_identifier: str | None = Field(default=None, max_length=4000)
    default_product_instructions: str | None = Field(default=None, max_length=4000)


class TelegramBotConfigPublic(BaseModel):
    id: UUID
    merchant_id: UUID
    bot_username: str | None
    discussion_group_id: int | None
    welcome_message: str | None
    language_preference: LanguagePref
    is_active: bool
    updated_at: datetime
    # Brand voice (Telegram-specific)
    business_type: str | None = None
    business_description: str | None = None
    system_prompt: str | None = None
    business_mode: BusinessMode = "PRODUCT_SALES"
    default_product_identifier: str | None = None
    default_product_instructions: str | None = None
    # token is never returned

    model_config = {"from_attributes": True}


class TelegramBotConfigInternal(BaseModel):
    """Returned only to the Telegram microservice via X-Service-Token."""
    merchant_id: UUID
    bot_token: str  # decrypted
    bot_username: str | None
    discussion_group_id: int | None
    welcome_message: str | None
    language_preference: LanguagePref
    is_active: bool

    # Channel binding (filled when bot promoted as channel admin)
    channel_id: int | None = None
    channel_username: str | None = None

    business_name: str
    business_type: str | None = None
    business_description: str | None = None
    system_prompt: str | None = None
    business_mode: BusinessMode = "PRODUCT_SALES"

    # AI agent fields (decrypted key for inter-service use only)
    ai_provider: str | None = None
    ai_api_key: str | None = None
    ai_model: str | None = None
    ai_auto_reply_dm: bool = False
    ai_auto_reply_comments: bool = False
    ai_parse_hashtag_products: bool = True

    # Default product context (inherited when per-product values are blank)
    default_product_identifier: str | None = None
    default_product_instructions: str | None = None
    # Active DM contacts the agent can reference in replies (ordered by position)
    dm_contacts: list[dict] = Field(default_factory=list)
    # Active payment accounts the agent can share with customers ready to pay
    payment_accounts: list[dict] = Field(default_factory=list)


BUSINESS_TYPE_PRESETS = [
    "Retail shop",
    "Restaurant / Cafe",
    "Online store",
    "Consultancy",
    "Service provider",
    "Tutoring / Education",
    "Healthcare / Clinic",
    "Real estate",
    "Other",
]
