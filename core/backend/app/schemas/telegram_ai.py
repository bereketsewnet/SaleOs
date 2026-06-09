from typing import Literal

from pydantic import BaseModel, Field

AIProvider = Literal["GEMINI", "OPENAI", "CLAUDE"]


class TelegramAISettingsUpdate(BaseModel):
    """All fields optional. Sending null clears."""
    ai_provider: AIProvider | None = None
    ai_api_key: str | None = Field(default=None, max_length=400)
    ai_model: str | None = Field(default=None, max_length=100)
    ai_auto_reply_dm: bool | None = None
    ai_auto_reply_comments: bool | None = None
    ai_parse_hashtag_products: bool | None = None


class TelegramAISettingsPublic(BaseModel):
    ai_provider: AIProvider | None = None
    # Key is never returned in plaintext — only whether one is configured.
    ai_api_key_set: bool = False
    ai_model: str | None = None
    ai_auto_reply_dm: bool = False
    ai_auto_reply_comments: bool = False
    ai_parse_hashtag_products: bool = True


# Default model per provider (merchant can override)
DEFAULT_MODELS: dict[str, str] = {
    "GEMINI": "gemini-2.0-flash",
    "OPENAI": "gpt-4.1-mini",
    "CLAUDE": "claude-haiku-4-5-20251001",
}
