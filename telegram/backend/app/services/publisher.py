from uuid import UUID

import httpx
import structlog
from aiogram import Bot
from aiogram.types import BufferedInputFile, InputMediaPhoto

from app.services.bot_manager import get_bot_manager
from app.services.core_client import CoreClient

logger = structlog.get_logger()


class PublisherError(Exception):
    pass


# Telegram caps a media group at 10 items.
_MEDIA_GROUP_LIMIT = 10


def _internal_image_url(url: str) -> str:
    """Browser-facing URLs point at localhost; swap to Docker internal host."""
    return url.replace("localhost:9000", "minio:9000")


def _html_escape(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def _format_caption(*, title: str, description: str | None, base_price: str | None) -> str:
    parts = [f"<b>{_html_escape(title)}</b>"]
    if description:
        parts.append(_html_escape(description))
    if base_price:
        parts.append(f"\n💰 <b>ETB {_html_escape(base_price)}</b>")
    return "\n".join(parts)


async def _download(url: str) -> bytes:
    internal_url = _internal_image_url(url)
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(internal_url)
        resp.raise_for_status()
        return resp.content


async def publish_product(
    *,
    merchant_id: UUID,
    product_id: UUID,
    title: str,
    description: str | None,
    base_price: str | None,
    image_urls: list[str],
) -> dict:
    bm = get_bot_manager()
    bundle = bm.get_bot_for_merchant(merchant_id)
    if bundle is None:
        raise PublisherError("bot_not_running")

    cfg = await CoreClient().get_telegram_config(merchant_id)
    if not cfg or not cfg.get("is_active"):
        raise PublisherError("bot_inactive")
    channel_id = cfg.get("channel_id")
    if not channel_id:
        raise PublisherError("channel_not_connected")

    bot: Bot = bundle.bot
    caption = _format_caption(title=title, description=description, base_price=base_price)

    # Cap to 10 (Telegram limit) and try to download each.
    photo_payloads: list[tuple[str, bytes]] = []
    for url in image_urls[:_MEDIA_GROUP_LIMIT]:
        try:
            photo_payloads.append((url, await _download(url)))
        except Exception as exc:
            logger.warning(
                "publisher_image_download_failed",
                merchant_id=str(merchant_id),
                product_id=str(product_id),
                url=url,
                error=str(exc),
            )

    sent_messages = []
    try:
        if len(photo_payloads) >= 2:
            media = []
            for idx, (_, b) in enumerate(photo_payloads):
                media.append(
                    InputMediaPhoto(
                        media=BufferedInputFile(b, filename=f"{idx}.jpg"),
                        caption=caption if idx == 0 else None,
                        parse_mode="HTML" if idx == 0 else None,
                    )
                )
            sent_messages = await bot.send_media_group(chat_id=channel_id, media=media)
        elif len(photo_payloads) == 1:
            sent = await bot.send_photo(
                chat_id=channel_id,
                photo=BufferedInputFile(photo_payloads[0][1], filename="0.jpg"),
                caption=caption,
                parse_mode="HTML",
            )
            sent_messages = [sent]
    except Exception as exc:
        logger.warning(
            "publisher_send_failed_falling_back_to_text",
            merchant_id=str(merchant_id),
            product_id=str(product_id),
            error=str(exc),
        )
        sent_messages = []

    if not sent_messages:
        sent = await bot.send_message(
            chat_id=channel_id,
            text=caption,
            parse_mode="HTML",
        )
        sent_messages = [sent]

    # The first message gets the product_id link. Other messages from the same
    # media group are recorded as posted_by_admin too (they belong to the same product).
    core = CoreClient()
    primary = sent_messages[0]
    primary_photo_id = primary.photo[-1].file_id if primary.photo else None
    await core.save_channel_post(
        merchant_id,
        channel_id=channel_id,
        message_id=primary.message_id,
        caption=caption,
        photo_file_id=primary_photo_id,
        posted_by_admin=True,
        product_id=product_id,
    )
    for extra in sent_messages[1:]:
        extra_photo_id = extra.photo[-1].file_id if extra.photo else None
        try:
            # Tag every message in the group with product_id so delete-product
            # can find the whole album to remove from Telegram.
            await core.save_channel_post(
                merchant_id,
                channel_id=channel_id,
                message_id=extra.message_id,
                caption=None,
                photo_file_id=extra_photo_id,
                posted_by_admin=True,
                product_id=product_id,
            )
        except Exception as exc:
            logger.warning("publisher_save_extra_failed", error=str(exc))

    return {
        "message_ids": [m.message_id for m in sent_messages],
        "channel_id": channel_id,
    }
