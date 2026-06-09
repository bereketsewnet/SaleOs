"""Discussion-group auto-reply handler. When a customer replies to a channel post
in the linked Discussion Group, the bot identifies which product the post belonged
to (via telegram_channel_posts) and the reply agent answers in the same group."""
from uuid import UUID

import structlog
from aiogram import F, Router
from aiogram.types import Message

from app.bot.context import BotMerchantContext
from app.bot.handlers.dm import _build_product_context
from app.services.core_client import CoreClient
from app.services.reply_agent import generate_reply

logger = structlog.get_logger()


def register(router: Router) -> None:
    @router.message(F.chat.type.in_({"supergroup", "group"}), F.reply_to_message)
    async def on_discussion_reply(
        message: Message, merchant: BotMerchantContext
    ) -> None:
        if not merchant.ai_auto_reply_comments:
            return
        if not merchant.ai_provider or not merchant.ai_api_key:
            return
        if not (message.text or message.caption):
            return

        # The reply_to_message in a linked Discussion Group has forward origin
        # pointing back to the channel post. Resolve product from that.
        reply_to = message.reply_to_message
        if reply_to is None:
            return

        channel_message_id: int | None = None
        # aiogram 3 exposes forward_from_chat / forward_from_message_id on legacy fields,
        # and forward_origin on newer ones. Try both.
        forward_chat_id: int | None = None
        if getattr(reply_to, "forward_from_chat", None) and getattr(
            reply_to, "forward_from_message_id", None
        ):
            forward_chat_id = reply_to.forward_from_chat.id
            channel_message_id = reply_to.forward_from_message_id
        else:
            origin = getattr(reply_to, "forward_origin", None)
            if origin is not None:
                forward_chat_id = getattr(getattr(origin, "chat", None), "id", None)
                channel_message_id = getattr(origin, "message_id", None)

        if not (forward_chat_id and channel_message_id):
            return
        if merchant.channel_id and forward_chat_id != merchant.channel_id:
            return

        product_id = await CoreClient().get_product_for_channel_message(
            merchant.merchant_id, forward_chat_id, channel_message_id
        )

        product_ctx = None
        if product_id is not None:
            try:
                product_ctx = await _build_product_context(product_id)
            except Exception as exc:
                logger.warning(
                    "comment_product_context_failed",
                    merchant_id=str(merchant.merchant_id),
                    product_id=str(product_id),
                    error=str(exc),
                )

        catalog: list[dict] = []
        try:
            catalog = await CoreClient().get_merchant_catalog(merchant.merchant_id)
        except Exception as exc:
            logger.warning(
                "comment_catalog_fetch_failed",
                merchant_id=str(merchant.merchant_id),
                error=str(exc),
            )

        reply = await generate_reply(
            merchant=merchant,
            customer_message=message.text or message.caption or "",
            product_ctx=product_ctx,
            surface="COMMENT",
            catalog=catalog,
        )
        # Reply in the same group, threaded under the customer's comment
        await message.reply(reply)
