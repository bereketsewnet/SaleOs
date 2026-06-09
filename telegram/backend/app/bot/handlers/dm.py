"""DM handlers — private one-on-one chat with the customer.

Three handler tiers (registered in order; aiogram dispatches the first match):
1. Photo + active buy flag → treat as a payment receipt; create an order and ask
   for phone/address.
2. Text + active pending-details flag → parse phone + address; update the order.
3. Anything else → AI agent (normal product/sales Q&A).
"""
import re
from decimal import Decimal
from io import BytesIO
from uuid import UUID

import structlog
from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.bot.context import BotMerchantContext
from app.bot.handlers.start import dm_buy_key
from app.core.redis import get_redis
from app.services.core_client import CoreClient
from app.services.reply_agent import ProductContext, generate_reply

logger = structlog.get_logger()


_PENDING_DETAILS_TTL = 60 * 60  # 1 hour

_PHONE_REGEX = re.compile(
    r"(?:\+?251|0)\s?[79]\d{2}[\s\-]?\d{3}[\s\-]?\d{3,4}"
)


def _pending_details_key(merchant_id: UUID, user_id: int) -> str:
    return f"tg:dm_pending_details:{merchant_id}:{user_id}"


def _extract_phone(text: str) -> str | None:
    if not text:
        return None
    match = _PHONE_REGEX.search(text)
    if not match:
        return None
    return re.sub(r"[\s\-]", "", match.group(0))


def _strip_phone(text: str, phone_raw: str) -> str:
    return re.sub(r"\s+", " ", text.replace(phone_raw, "")).strip(" ,—-:|")


def register(router: Router) -> None:
    # === 1. Photo in DM while buy-flag is active → receipt ===
    @router.message(F.chat.type == "private", F.photo)
    async def on_dm_receipt(
        message: Message, merchant: BotMerchantContext, bot: Bot
    ) -> None:
        if message.from_user is None:
            return
        redis = await get_redis()
        product_id_raw = await redis.get(
            dm_buy_key(merchant.merchant_id, message.from_user.id)
        )
        if not product_id_raw:
            # No active buy flow → ignore (don't accidentally create orders from random pics).
            await message.answer(
                "Thanks for the photo. If this is a payment screenshot, please start the "
                "buy flow from the product page first so I know what to attach it to."
            )
            return
        try:
            product_id = UUID(product_id_raw)
        except Exception:
            await redis.delete(
                dm_buy_key(merchant.merchant_id, message.from_user.id)
            )
            return

        try:
            file_id = message.photo[-1].file_id
            tg_file = await bot.get_file(file_id)
            buf = BytesIO()
            await bot.download_file(tg_file.file_path, destination=buf)
            buf.seek(0)
            data = buf.read()
        except Exception as exc:
            logger.warning(
                "dm_receipt_download_failed",
                merchant_id=str(merchant.merchant_id),
                error=str(exc),
            )
            await message.answer("Hmm, I couldn't download that image. Please try again.")
            return

        customer_name = (
            getattr(message.from_user, "full_name", None)
            or message.from_user.first_name
        )
        try:
            result = await CoreClient().create_order_from_channel_comment(
                merchant_id=merchant.merchant_id,
                product_id=product_id,
                telegram_user_id=message.from_user.id,
                customer_name=customer_name,
                receipt_bytes=data,
                receipt_filename=f"dm-receipt-{message.message_id}.jpg",
            )
        except Exception as exc:
            logger.warning(
                "dm_receipt_order_failed",
                merchant_id=str(merchant.merchant_id),
                product_id=str(product_id),
                error=str(exc),
            )
            await message.answer(
                "Got your screenshot but something went wrong creating the order. Our team will reach out."
            )
            return

        # Clear buy flag; set pending-details flag.
        await redis.delete(dm_buy_key(merchant.merchant_id, message.from_user.id))
        order_id = result["order_id"]
        await redis.set(
            _pending_details_key(merchant.merchant_id, message.from_user.id),
            order_id,
            ex=_PENDING_DETAILS_TTL,
        )
        await message.answer(
            f"✅ Got your payment screenshot — order #{order_id[:8]} is created.\n\n"
            f"To finish, please reply with your *phone number* and *delivery address*.\n"
            f"Example: `+251911223344 — Bole, Addis Ababa`",
            parse_mode="Markdown",
        )

    # === 2. Text in DM while pending-details flag is active → capture phone+address ===
    @router.message(
        F.chat.type == "private",
        ~F.text.startswith("/"),
    )
    async def on_dm_text(
        message: Message, merchant: BotMerchantContext, state: FSMContext
    ) -> None:
        if not message.text and not message.caption:
            return
        if message.from_user is None:
            return
        text = (message.text or message.caption or "").strip()

        redis = await get_redis()
        pending_key = _pending_details_key(merchant.merchant_id, message.from_user.id)
        pending_order_id = await redis.get(pending_key)
        if pending_order_id:
            phone = _extract_phone(text)
            if not phone:
                await message.answer(
                    "I couldn't find a phone number in your message. "
                    "Please send it like `+251911223344 — Bole, Addis Ababa`",
                    parse_mode="Markdown",
                )
                return
            address = _strip_phone(text, _PHONE_REGEX.search(text).group(0))
            if not address:
                address = None
            customer_name = (
                getattr(message.from_user, "full_name", None)
                or message.from_user.first_name
            )
            try:
                await CoreClient().update_order_customer_details(
                    order_id=UUID(pending_order_id),
                    name=customer_name,
                    phone=phone,
                    address=address,
                )
            except Exception as exc:
                logger.warning(
                    "dm_pending_details_update_failed",
                    merchant_id=str(merchant.merchant_id),
                    error=str(exc),
                )
                await message.answer(
                    "Thanks — something went wrong saving your details. Our team will reach out."
                )
                return
            await redis.delete(pending_key)
            address_line = f"\nAddress: {address}" if address else ""
            await message.answer(
                f"Got it ✓\nPhone: {phone}{address_line}\n\n"
                f"We'll review your payment and message you back as soon as it's verified."
            )
            return

        # === 3. Fall through to AI agent ===
        if not merchant.ai_auto_reply_dm:
            return
        if not merchant.ai_provider or not merchant.ai_api_key:
            return

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
            customer_message=text,
            product_ctx=product_ctx,
            surface="DM",
            catalog=catalog,
        )
        await message.answer(reply, disable_web_page_preview=True)


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
