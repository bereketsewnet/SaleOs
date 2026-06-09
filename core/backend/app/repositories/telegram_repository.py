from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.telegram import TelegramBotConfig


class TelegramBotConfigRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_merchant(self, merchant_id: UUID) -> TelegramBotConfig | None:
        result = await self.db.execute(
            select(TelegramBotConfig).where(TelegramBotConfig.merchant_id == merchant_id)
        )
        return result.scalar_one_or_none()

    async def list_active(self) -> list[TelegramBotConfig]:
        result = await self.db.execute(
            select(TelegramBotConfig).where(TelegramBotConfig.is_active.is_(True))
        )
        return list(result.scalars().all())

    async def upsert(
        self,
        *,
        merchant_id: UUID,
        encrypted_token: str,
        bot_username: str | None,
        language_preference: str,
        welcome_message: str | None,
    ) -> TelegramBotConfig:
        existing = await self.get_by_merchant(merchant_id)
        if existing:
            # Only connection-related fields. Brand voice is preserved.
            existing.bot_token = encrypted_token
            existing.bot_username = bot_username
            existing.language_preference = language_preference
            existing.welcome_message = welcome_message
            existing.is_active = True
            await self.db.flush()
            await self.db.refresh(existing)
            return existing

        config = TelegramBotConfig(
            merchant_id=merchant_id,
            bot_token=encrypted_token,
            bot_username=bot_username,
            language_preference=language_preference,
            welcome_message=welcome_message,
            is_active=True,
        )
        self.db.add(config)
        await self.db.flush()
        await self.db.refresh(config)
        return config

    async def update_brand_voice(
        self,
        merchant_id: UUID,
        *,
        business_type: str | None,
        business_description: str | None,
        system_prompt: str | None,
        business_mode: str | None = None,
        default_product_identifier: str | None = None,
        default_product_instructions: str | None = None,
    ) -> TelegramBotConfig | None:
        existing = await self.get_by_merchant(merchant_id)
        if not existing:
            return None
        if business_type is not None:
            existing.business_type = business_type or None
        if business_description is not None:
            existing.business_description = business_description or None
        if system_prompt is not None:
            existing.system_prompt = system_prompt or None
        if business_mode is not None:
            existing.business_mode = business_mode
        if default_product_identifier is not None:
            existing.default_product_identifier = default_product_identifier or None
        if default_product_instructions is not None:
            existing.default_product_instructions = default_product_instructions or None
        await self.db.flush()
        await self.db.refresh(existing)
        return existing

    async def update_ai_settings(
        self,
        merchant_id: UUID,
        *,
        ai_provider: str | None = None,
        ai_api_key_encrypted: str | None = None,
        clear_api_key: bool = False,
        ai_model: str | None = None,
        ai_auto_reply_dm: bool | None = None,
        ai_auto_reply_comments: bool | None = None,
        ai_parse_hashtag_products: bool | None = None,
    ) -> TelegramBotConfig | None:
        existing = await self.get_by_merchant(merchant_id)
        if not existing:
            return None
        if ai_provider is not None:
            existing.ai_provider = ai_provider or None
        if clear_api_key:
            existing.ai_api_key = None
        elif ai_api_key_encrypted is not None:
            existing.ai_api_key = ai_api_key_encrypted
        if ai_model is not None:
            existing.ai_model = ai_model or None
        if ai_auto_reply_dm is not None:
            existing.ai_auto_reply_dm = ai_auto_reply_dm
        if ai_auto_reply_comments is not None:
            existing.ai_auto_reply_comments = ai_auto_reply_comments
        if ai_parse_hashtag_products is not None:
            existing.ai_parse_hashtag_products = ai_parse_hashtag_products
        await self.db.flush()
        await self.db.refresh(existing)
        return existing

    async def delete_by_merchant(self, merchant_id: UUID) -> bool:
        existing = await self.get_by_merchant(merchant_id)
        if not existing:
            return False
        await self.db.delete(existing)
        await self.db.flush()
        return True
