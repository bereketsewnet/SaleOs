"""DM auto-reply handler. Fires on private chats that are NOT commands.
Loads the current product context (if any), calls the reply agent, sends the reply."""
from uuid import UUID

import structlog
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.bot.context import BotMerchantContext
from app.services.core_client import CoreClient
from app.services.reply_agent import ProductContext, generate_reply

logger = structlog.get_logger()


def register(router: Router) -> None:
    @router.message(F.chat.type == "private", ~F.text.startswith("/"))
    async def on_dm(
        message: Message, merchant: BotMerchantContext, state: FSMContext
    ) -> None:
        if not merchant.ai_auto_reply_dm:
            return
        if not merchant.ai_provider or not merchant.ai_api_key:
            return
        if not message.text and not message.caption:
            return

        # Did the customer arrive via /start product_X earlier?
        data = await state.get_data()
        product_id_raw = data.get("current_product_id")
        product_ctx: ProductContext | None = None
        if product_id_raw:
            try:
                product_ctx = await _build_product_context(UUID(str(product_id_raw)))
            except Exception as exc:
                logger.warning(
                    "dm_product_context_failed",
                    merchant_id=str(merchant.merchant_id),
                    product_id=str(product_id_raw),
                    error=str(exc),
                )

        catalog: list[dict] = []
        try:
            catalog = await CoreClient().get_merchant_catalog(merchant.merchant_id)
        except Exception as exc:
            logger.warning(
                "dm_catalog_fetch_failed",
                merchant_id=str(merchant.merchant_id),
                error=str(exc),
            )

        reply = await generate_reply(
            merchant=merchant,
            customer_message=message.text or message.caption or "",
            product_ctx=product_ctx,
            surface="DM",
            catalog=catalog,
        )
        await message.answer(reply, disable_web_page_preview=True)


async def _build_product_context(product_id: UUID) -> ProductContext | None:
    data = await CoreClient().get_product_agent_context(product_id)
    if not data:
        return None
    from decimal import Decimal

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
