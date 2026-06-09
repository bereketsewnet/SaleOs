"""Detects `#product` in manual channel posts → parses via AI → creates a Product.

Channel-post updates from a media group arrive one-by-one. We buffer them
keyed by (chat_id, media_group_id) for ~3 seconds, then process the group as one.
"""
import asyncio
import re
from io import BytesIO
from typing import Any
from uuid import UUID

import structlog
from aiogram import Bot
from aiogram.types import Message

from app.bot.context import BotMerchantContext
from app.services.ai_provider import AIError, complete_json
from app.services.core_client import CoreClient

logger = structlog.get_logger()

_HASHTAG_RE = re.compile(r"#product\b", re.IGNORECASE)
_BUFFER: dict[str, dict[str, Any]] = {}
_BUFFER_LOCK = asyncio.Lock()
_DEBOUNCE_SECONDS = 3.0


SYSTEM_PROMPT = (
    "You extract product details from a short Telegram channel post written by a "
    "small business. Return STRICT JSON with these keys: title (string, required, "
    "max 120 chars), description (string or null), base_price (number or null — "
    "extract numeric value only, no currency symbol). If the user just dropped "
    "an image with `#product` and no other info, infer a sensible title from the "
    "context; never invent a price."
)


def message_has_product_hashtag(message: Message) -> bool:
    text = message.caption or message.text or ""
    return bool(_HASHTAG_RE.search(text))


async def handle_channel_post(message: Message, merchant: BotMerchantContext, bot: Bot) -> None:
    """Decide whether this post is a `#product` import; buffer media groups."""
    if not merchant.ai_parse_hashtag_products:
        return
    if not message_has_product_hashtag(message):
        return
    if not (merchant.ai_provider and merchant.ai_api_key):
        logger.info(
            "hashtag_import_skipped_no_ai",
            merchant_id=str(merchant.merchant_id),
            message_id=message.message_id,
        )
        return

    media_group_id = message.media_group_id
    key = f"{message.chat.id}:{media_group_id}" if media_group_id else f"{message.chat.id}:{message.message_id}"

    async with _BUFFER_LOCK:
        bucket = _BUFFER.get(key)
        if bucket is None:
            bucket = {
                "messages": [],
                "task": None,
                "merchant": merchant,
                "bot": bot,
            }
            _BUFFER[key] = bucket
        bucket["messages"].append(message)
        if bucket["task"] is None or bucket["task"].done():
            bucket["task"] = asyncio.create_task(_flush_after_debounce(key))


async def _flush_after_debounce(key: str) -> None:
    await asyncio.sleep(_DEBOUNCE_SECONDS)
    async with _BUFFER_LOCK:
        bucket = _BUFFER.pop(key, None)
    if bucket is None:
        return
    try:
        await _process_group(bucket["messages"], bucket["merchant"], bucket["bot"])
    except Exception as exc:
        logger.warning(
            "hashtag_import_failed",
            key=key,
            error_type=type(exc).__name__,
            error=str(exc),
        )


async def _process_group(messages: list[Message], merchant: BotMerchantContext, bot: Bot) -> None:
    messages = sorted(messages, key=lambda m: m.message_id)
    primary = messages[0]
    related_ids = [m.message_id for m in messages[1:]]
    caption_text = primary.caption or primary.text or ""

    parsed = await _ai_parse(merchant, caption_text)
    title = (parsed.get("title") or "").strip()
    if not title:
        title = "Untitled product"
    description = parsed.get("description")
    base_price = parsed.get("base_price")
    base_price_str: str | None
    try:
        base_price_str = str(float(base_price)) if base_price is not None else None
    except (TypeError, ValueError):
        base_price_str = None

    # Upload each photo to MinIO via Core internal endpoint.
    image_urls: list[str] = []
    core = CoreClient()
    for idx, m in enumerate(messages):
        if not m.photo:
            continue
        try:
            file_id = m.photo[-1].file_id
            tg_file = await bot.get_file(file_id)
            buf = BytesIO()
            await bot.download_file(tg_file.file_path, destination=buf)
            buf.seek(0)
            data = buf.read()
            uploaded = await core.upload_product_image(
                merchant.merchant_id,
                filename=f"{m.message_id}.jpg",
                data=data,
                content_type="image/jpeg",
            )
            image_urls.append(uploaded["url"])
        except Exception as exc:
            logger.warning(
                "hashtag_import_image_failed",
                merchant_id=str(merchant.merchant_id),
                message_id=m.message_id,
                error=str(exc),
            )

    result = await core.create_product_from_channel_post(
        merchant.merchant_id,
        channel_id=primary.chat.id,
        primary_message_id=primary.message_id,
        related_message_ids=related_ids,
        title=title,
        description=description,
        base_price=base_price_str,
        image_urls=image_urls,
    )
    logger.info(
        "hashtag_import_created",
        merchant_id=str(merchant.merchant_id),
        product_id=result.get("id"),
        message_ids=[primary.message_id, *related_ids],
        images=len(image_urls),
    )

    # If AI is configured and the product has images but no identifier yet,
    # fire off the OCR vision pipeline. Reuses the same internal endpoint Core uses.
    if (
        merchant.ai_provider
        and merchant.ai_api_key
        and image_urls
        and not result.get("is_ocr_identified")
    ):
        try:
            from app.api.v1.ocr import OCRProductRequest, _run as _ocr_run

            from uuid import UUID

            await _ocr_run(
                OCRProductRequest(
                    merchant_id=merchant.merchant_id,
                    product_id=UUID(result["id"]),
                    image_urls=image_urls,
                )
            )
        except Exception as exc:
            logger.warning(
                "hashtag_ocr_kickoff_failed",
                merchant_id=str(merchant.merchant_id),
                error=str(exc),
            )


async def _ai_parse(merchant: BotMerchantContext, caption_text: str) -> dict[str, Any]:
    user_prompt = (
        "Parse this Telegram channel post into product fields. "
        "Return ONLY a JSON object — no prose, no markdown.\n\n"
        f"POST:\n{caption_text}\n\n"
        'Schema: {"title": str, "description": str|null, "base_price": number|null}'
    )
    try:
        return await complete_json(
            provider=merchant.ai_provider or "",
            api_key=merchant.ai_api_key or "",
            model=merchant.ai_model,
            system_prompt=SYSTEM_PROMPT,
            user_prompt=user_prompt,
        )
    except AIError as exc:
        logger.warning(
            "hashtag_ai_parse_failed",
            merchant_id=str(merchant.merchant_id),
            error=str(exc),
        )
        return _regex_fallback(caption_text)


_PRICE_RE = re.compile(
    r"(?:price\s*[:\-]?\s*)?(\d[\d,]*(?:\.\d+)?)\s*(?:etb|birr|br|\.?)\b",
    re.IGNORECASE,
)


def _regex_fallback(caption_text: str) -> dict[str, Any]:
    """Best-effort parse without AI — title = first useful line; price = first number."""
    title = "Untitled product"
    desc_lines: list[str] = []
    for raw in caption_text.splitlines():
        cleaned = _HASHTAG_RE.sub("", raw).strip()
        if not cleaned:
            continue
        if title == "Untitled product":
            title = cleaned[:120]
        else:
            desc_lines.append(cleaned)

    price = None
    m = _PRICE_RE.search(caption_text)
    if m:
        try:
            price = float(m.group(1).replace(",", ""))
        except ValueError:
            price = None

    return {
        "title": title,
        "description": "\n".join(desc_lines) or None,
        "base_price": price,
    }
