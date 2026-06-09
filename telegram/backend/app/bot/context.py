from dataclasses import dataclass, field
from uuid import UUID


@dataclass(frozen=True)
class BotMerchantContext:
    """Per-merchant context injected into every aiogram handler via middleware."""
    merchant_id: UUID
    bot_username: str | None
    welcome_message: str | None
    language_preference: str
    business_name: str | None = None
    business_type: str | None = None
    business_description: str | None = None
    system_prompt: str | None = None
    # AI agent config (forwarded by bot_manager from Core internal config response)
    ai_provider: str | None = None
    ai_api_key: str | None = None
    ai_model: str | None = None
    ai_auto_reply_dm: bool = False
    ai_auto_reply_comments: bool = False
    ai_parse_hashtag_products: bool = True
    # Channel binding
    channel_id: int | None = None
    # Defaults inherited by every product whose own identifier/instructions are blank
    default_product_identifier: str | None = None
    default_product_instructions: str | None = None
    # Active DM contacts (ordered by position, only is_active=True)
    dm_contacts: list[dict] = field(default_factory=list)
    # Active payment accounts (bank info) the agent shares with paying customers
    payment_accounts: list[dict] = field(default_factory=list)
