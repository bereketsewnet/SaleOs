"""Channel-related handlers:
- my_chat_member: detect when bot is added/promoted as channel admin → auto-bind.
- channel_post: capture every post in the merchant's channel → save to DB.
  Also routes #product-tagged posts to the hashtag importer.
"""
import structlog
from aiogram import Bot, F, Router
from aiogram.types import ChatMemberUpdated, Message

from app.bot.context import BotMerchantContext
from app.services.core_client import CoreClient
from app.services.hashtag_importer import handle_channel_post as handle_hashtag_post

logger = structlog.get_logger()


def register(router: Router) -> None:
    @router.my_chat_member(F.chat.type == "channel")
    async def on_channel_promotion(
        event: ChatMemberUpdated, merchant: BotMerchantContext
    ) -> None:
        """Fires when the bot's membership status changes in a channel.
        If the bot is now an admin, persist this channel as the merchant's channel."""
        new_status = event.new_chat_member.status if event.new_chat_member else None
        if new_status not in ("administrator", "creator"):
            return

        chat = event.chat
        try:
            await CoreClient().bind_channel(
                merchant.merchant_id,
                channel_id=chat.id,
                channel_username=chat.username,
                channel_title=chat.title,
            )
            logger.info(
                "channel_auto_bound",
                merchant_id=str(merchant.merchant_id),
                channel_id=chat.id,
                channel_username=chat.username,
            )
        except Exception as exc:
            logger.warning(
                "channel_bind_failed",
                merchant_id=str(merchant.merchant_id),
                channel_id=chat.id,
                error=str(exc),
            )

    @router.channel_post()
    async def on_channel_post(
        message: Message, merchant: BotMerchantContext, bot: Bot
    ) -> None:
        """Every new post in the merchant's channel arrives here (bot must be admin)."""
        photo_file_id = None
        if message.photo:
            photo_file_id = message.photo[-1].file_id
        caption = message.caption or message.text

        try:
            await CoreClient().save_channel_post(
                merchant.merchant_id,
                channel_id=message.chat.id,
                message_id=message.message_id,
                caption=caption,
                photo_file_id=photo_file_id,
            )
        except Exception as exc:
            logger.warning(
                "channel_post_save_failed",
                merchant_id=str(merchant.merchant_id),
                channel_id=message.chat.id,
                message_id=message.message_id,
                error=str(exc),
            )

        # Manual #product import — runs in the background, buffered for media groups.
        try:
            await handle_hashtag_post(message, merchant, bot)
        except Exception as exc:
            logger.warning(
                "hashtag_handler_failed",
                merchant_id=str(merchant.merchant_id),
                error=str(exc),
            )
