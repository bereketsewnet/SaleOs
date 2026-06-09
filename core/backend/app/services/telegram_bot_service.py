from uuid import UUID

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.telegram import TelegramBotConfig
from app.repositories.merchant_repository import MerchantRepository
from app.repositories.payment_account_repository import PaymentAccountRepository
from app.repositories.telegram_dm_contact_repository import TelegramDMContactRepository
from app.repositories.telegram_repository import TelegramBotConfigRepository
from app.schemas.telegram_ai import (
    DEFAULT_MODELS,
    TelegramAISettingsPublic,
    TelegramAISettingsUpdate,
)
from app.schemas.telegram_config import (
    TelegramBotConfigUpsert,
    TelegramBrandVoiceUpdate,
)
from app.utils.crypto import decrypt_secret, encrypt_secret


class TelegramTokenInvalidError(Exception):
    pass


class TelegramConfigNotFoundError(Exception):
    pass


class TelegramBotService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = TelegramBotConfigRepository(db)

    async def get_for_merchant(self, merchant_id: UUID) -> TelegramBotConfig | None:
        return await self.repo.get_by_merchant(merchant_id)

    async def upsert(
        self, merchant_id: UUID, payload: TelegramBotConfigUpsert
    ) -> TelegramBotConfig:
        bot_username = await self._validate_token(payload.bot_token)
        encrypted = encrypt_secret(payload.bot_token)
        return await self.repo.upsert(
            merchant_id=merchant_id,
            encrypted_token=encrypted,
            bot_username=bot_username,
            language_preference=payload.language_preference,
            welcome_message=payload.welcome_message,
        )

    async def update_brand_voice(
        self, merchant_id: UUID, payload: TelegramBrandVoiceUpdate
    ) -> TelegramBotConfig | None:
        return await self.repo.update_brand_voice(
            merchant_id,
            business_type=payload.business_type,
            business_description=payload.business_description,
            system_prompt=payload.system_prompt,
            default_product_identifier=payload.default_product_identifier,
            default_product_instructions=payload.default_product_instructions,
        )

    async def delete(self, merchant_id: UUID) -> bool:
        return await self.repo.delete_by_merchant(merchant_id)

    async def get_ai_settings(self, merchant_id: UUID) -> TelegramAISettingsPublic | None:
        cfg = await self.repo.get_by_merchant(merchant_id)
        if not cfg:
            return None
        return TelegramAISettingsPublic(
            ai_provider=cfg.ai_provider,
            ai_api_key_set=bool(cfg.ai_api_key),
            ai_model=cfg.ai_model,
            ai_auto_reply_dm=cfg.ai_auto_reply_dm,
            ai_auto_reply_comments=cfg.ai_auto_reply_comments,
            ai_parse_hashtag_products=cfg.ai_parse_hashtag_products,
        )

    async def update_ai_settings(
        self, merchant_id: UUID, payload: TelegramAISettingsUpdate
    ) -> TelegramAISettingsPublic | None:
        # API key handling: empty string → clear; non-empty → encrypt and store;
        # None → leave alone.
        encrypted = None
        clear_key = False
        if payload.ai_api_key is not None:
            stripped = payload.ai_api_key.strip()
            if stripped == "":
                clear_key = True
            else:
                encrypted = encrypt_secret(stripped)

        # If model is empty but provider was just set, pick a sensible default.
        model = payload.ai_model
        if model is None and payload.ai_provider is not None:
            model = DEFAULT_MODELS.get(payload.ai_provider)

        cfg = await self.repo.update_ai_settings(
            merchant_id,
            ai_provider=payload.ai_provider,
            ai_api_key_encrypted=encrypted,
            clear_api_key=clear_key,
            ai_model=model,
            ai_auto_reply_dm=payload.ai_auto_reply_dm,
            ai_auto_reply_comments=payload.ai_auto_reply_comments,
            ai_parse_hashtag_products=payload.ai_parse_hashtag_products,
        )
        if not cfg:
            return None
        return TelegramAISettingsPublic(
            ai_provider=cfg.ai_provider,
            ai_api_key_set=bool(cfg.ai_api_key),
            ai_model=cfg.ai_model,
            ai_auto_reply_dm=cfg.ai_auto_reply_dm,
            ai_auto_reply_comments=cfg.ai_auto_reply_comments,
            ai_parse_hashtag_products=cfg.ai_parse_hashtag_products,
        )

    async def get_internal(self, merchant_id: UUID) -> dict | None:
        config = await self.repo.get_by_merchant(merchant_id)
        if not config:
            return None
        merchant = await MerchantRepository(self.db).get_by_id(merchant_id)
        return {
            "merchant_id": config.merchant_id,
            "bot_token": decrypt_secret(config.bot_token),
            "bot_username": config.bot_username,
            "discussion_group_id": config.discussion_group_id,
            "welcome_message": config.welcome_message,
            "language_preference": config.language_preference,
            "is_active": config.is_active,
            "channel_id": config.channel_id,
            "channel_username": config.channel_username,
            "business_name": merchant.business_name if merchant else "",
            "business_type": config.business_type,
            "business_description": config.business_description,
            "system_prompt": config.system_prompt,
            "ai_provider": config.ai_provider,
            "ai_api_key": decrypt_secret(config.ai_api_key) if config.ai_api_key else None,
            "ai_model": config.ai_model,
            "ai_auto_reply_dm": config.ai_auto_reply_dm,
            "ai_auto_reply_comments": config.ai_auto_reply_comments,
            "ai_parse_hashtag_products": config.ai_parse_hashtag_products,
            "default_product_identifier": config.default_product_identifier,
            "default_product_instructions": config.default_product_instructions,
            "dm_contacts": [
                {
                    "id": str(c.id),
                    "kind": c.kind,
                    "value": c.value,
                    "label": c.label,
                    "position": c.position,
                }
                for c in await TelegramDMContactRepository(self.db).list_active(merchant_id)
            ],
            "payment_accounts": [
                {
                    "bank_name": p.bank_name,
                    "account_number": p.account_number,
                    "account_holder_name": p.account_holder_name,
                    "phone": p.phone,
                }
                for p in await PaymentAccountRepository(self.db).list_by_merchant(merchant_id)
                if p.is_active
            ],
        }

    async def _validate_token(self, token: str) -> str:
        url = f"https://api.telegram.org/bot{token}/getMe"
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(url)
        except httpx.HTTPError as exc:
            raise TelegramTokenInvalidError("telegram_unreachable") from exc
        if resp.status_code != 200:
            raise TelegramTokenInvalidError("invalid_token")
        data = resp.json()
        if not data.get("ok"):
            raise TelegramTokenInvalidError("invalid_token")
        return data["result"].get("username")

    @staticmethod
    async def notify_telegram_service(merchant_id: UUID) -> None:
        """Called as a FastAPI BackgroundTask AFTER DB commit."""
        url = f"{settings.TELEGRAM_SERVICE_URL}/api/v1/telegram/internal/reload-bot/{merchant_id}"
        headers = {"X-Service-Token": settings.X_SERVICE_TOKEN}
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                await client.post(url, headers=headers)
        except httpx.HTTPError:
            pass
