"""Editable merchant identity. Lives on the `merchants` table — shared across
all channels (Telegram, future TikTok/IG/FB). The bot's BotMerchantContext
pulls business_name from here, so a change reloads the bot too."""
from pydantic import BaseModel, EmailStr, Field


class MerchantProfileUpdate(BaseModel):
    """Send only the fields you want to change."""
    business_name: str | None = Field(default=None, min_length=2, max_length=255)
    contact_email: EmailStr | None = None
    contact_phone: str | None = Field(default=None, min_length=4, max_length=30)


class MerchantProfilePublic(BaseModel):
    business_name: str
    contact_email: str
    contact_phone: str
    is_active: bool

    model_config = {"from_attributes": True}
