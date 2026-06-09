"""Mini App chat — reuses the bot's BotMerchantContext (so brand voice + DM contacts
+ payment accounts + AI key are already loaded). Falls back to a one-off fetch
if the bot isn't currently polling for that merchant."""
from decimal import Decimal
from uuid import UUID

import structlog

from app.bot.context import BotMerchantContext
from app.services.bot_manager import get_bot_manager
from app.services.core_client import CoreClient
from app.services.reply_agent import ProductContext, generate_reply

logger = structlog.get_logger()


async def _build_merchant_context(merchant_id: UUID) -> BotMerchantContext | None:
    """Prefer the live, hot context from the bot manager. If the bot isn't
    running (e.g. token revoked), do a one-shot fetch from Core."""
    bundle = get_bot_manager().get_bot_for_merchant(merchant_id)
    if bundle is not None:
        m = bundle.dispatcher["merchant"]
        if isinstance(m, BotMerchantContext):
            return m
    # Fallback: fetch + assemble
    cfg = await CoreClient().get_telegram_config(merchant_id)
    if not cfg:
        return None
    return BotMerchantContext(
        merchant_id=merchant_id,
        bot_username=cfg.get("bot_username"),
        welcome_message=cfg.get("welcome_message"),
        language_preference=cfg.get("language_preference") or "AUTO",
        business_name=cfg.get("business_name"),
        business_type=cfg.get("business_type"),
        business_description=cfg.get("business_description"),
        system_prompt=cfg.get("system_prompt"),
        ai_provider=cfg.get("ai_provider"),
        ai_api_key=cfg.get("ai_api_key"),
        ai_model=cfg.get("ai_model"),
        ai_auto_reply_dm=cfg.get("ai_auto_reply_dm", False),
        ai_auto_reply_comments=cfg.get("ai_auto_reply_comments", False),
        ai_parse_hashtag_products=cfg.get("ai_parse_hashtag_products", True),
        channel_id=cfg.get("channel_id"),
        default_product_identifier=cfg.get("default_product_identifier"),
        default_product_instructions=cfg.get("default_product_instructions"),
        dm_contacts=cfg.get("dm_contacts") or [],
        payment_accounts=cfg.get("payment_accounts") or [],
    )


async def _build_product_context(product_id: UUID) -> ProductContext | None:
    data = await CoreClient().get_product_agent_context(product_id)
    if not data:
        return None
    return ProductContext(
        product_id=UUID(data["product_id"]),
        merchant_id=UUID(data["merchant_id"]),
        title=data["title"],
        description=data.get("description"),
        base_price=Decimal(str(data["base_price"])) if data.get("base_price") is not None else None,
        image_urls=list(data.get("image_urls") or []),
        identifier_effective=data.get("identifier_effective"),
        instructions_effective=data.get("instructions_effective"),
        is_ocr_identified=bool(data.get("is_ocr_identified")),
    )


async def generate_chat_reply(
    *,
    merchant_id: UUID,
    telegram_user_id: int,
    product_id: UUID | None,
    message: str,
    history: list[dict],
) -> str:
    merchant = await _build_merchant_context(merchant_id)
    if merchant is None:
        return "Sorry — this shop isn't fully set up yet. Please try again later."

    product_ctx: ProductContext | None = None
    if product_id:
        try:
            product_ctx = await _build_product_context(product_id)
        except Exception as exc:
            logger.warning(
                "chat_product_context_failed",
                merchant_id=str(merchant_id),
                product_id=str(product_id),
                error=str(exc),
            )

    catalog: list[dict] = []
    try:
        catalog = await CoreClient().get_merchant_catalog(merchant_id)
    except Exception as exc:
        logger.warning(
            "chat_catalog_fetch_failed",
            merchant_id=str(merchant_id),
            error=str(exc),
        )

    return await generate_reply(
        merchant=merchant,
        customer_message=message,
        product_ctx=product_ctx,
        surface="MINI_APP",
        catalog=catalog,
        history=history,
    )
