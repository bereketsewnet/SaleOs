"""Discussion-group handlers (public comments under channel posts).

Privacy boundary:
- This handler ONLY answers product questions publicly.
- When a customer shows buy intent, the bot replies with a deep link to the
  private bot DM. ALL payment / receipt / phone / address flow happens there.
- We never share bank info, account numbers, or accept receipts in public.

Also maintained here: a Redis mapping `tg:thread:{merchant}:{discussion_chat}:{thread_msg_id} → product_id`
populated when the channel auto-forwards a post into the linked discussion group, so any
later comment in that thread can resolve to the right product even if it replies
to the bot's message instead of the channel post.
"""
from uuid import UUID

import structlog
from aiogram import F, Router
from aiogram.types import Message

from app.bot.context import BotMerchantContext
from app.bot.handlers.dm import _build_product_context
from app.core.redis import get_redis
from app.services.core_client import CoreClient
from app.services.reply_agent import generate_reply

logger = structlog.get_logger()


_THREAD_MAP_TTL = 60 * 60 * 24 * 30  # 30 days

# Keywords that signal the customer wants to buy. Matched case-insensitively
# against the customer's message (English + Amharic). On a hit we redirect to
# the private bot DM instead of answering via AI in public.
_BUY_INTENT_KEYWORDS = [
    "buy",
    "purchase",
    "order",
    "pay",
    "payment",
    "want",
    "interested",
    "send me",
    "i'll take",
    "ill take",
    "how much",
    "price",
    # Amharic
    "ግዛ",
    "ልግዛ",
    "እፈልጋለሁ",
    "ስንት",
    "ዋጋ",
    "ክፈል",
]


def _thread_map_key(merchant_id: UUID, discussion_chat_id: int, thread_msg_id: int) -> str:
    return f"tg:thread:{merchant_id}:{discussion_chat_id}:{thread_msg_id}"


def _customer_shows_buy_intent(text: str) -> bool:
    if not text:
        return False
    lo = text.lower()
    return any(kw in lo for kw in _BUY_INTENT_KEYWORDS)


def _thread_id(message: Message) -> int | None:
    tid = getattr(message, "message_thread_id", None)
    if tid is None and message.reply_to_message is not None:
        tid = message.reply_to_message.message_id
    return tid


def _extract_channel_forward(message: Message) -> tuple[int, int] | None:
    if getattr(message, "forward_from_chat", None) and getattr(
        message, "forward_from_message_id", None
    ):
        return message.forward_from_chat.id, message.forward_from_message_id
    origin = getattr(message, "forward_origin", None)
    if origin is not None:
        chat = getattr(origin, "chat", None)
        mid = getattr(origin, "message_id", None)
        if chat is not None and mid is not None:
            return chat.id, mid
    return None


async def _resolve_product_for_thread(
    message: Message, merchant: BotMerchantContext
) -> UUID | None:
    """Try, in order: (1) reply chain, (2) Redis thread→product map,
    (3) most-recent published product as a last-resort guess."""
    reply_to = message.reply_to_message
    if reply_to is not None:
        fwd = _extract_channel_forward(reply_to)
        if fwd is not None:
            chat_id, msg_id = fwd
            if not merchant.channel_id or chat_id == merchant.channel_id:
                pid = await CoreClient().get_product_for_channel_message(
                    merchant.merchant_id, chat_id, msg_id
                )
                if pid is not None:
                    return pid

    thread_id = _thread_id(message)
    if thread_id is not None:
        redis = await get_redis()
        raw = await redis.get(
            _thread_map_key(merchant.merchant_id, message.chat.id, thread_id)
        )
        if raw:
            try:
                return UUID(raw)
            except Exception:
                pass

    try:
        catalog = await CoreClient().get_merchant_catalog(merchant.merchant_id, limit=1)
        if catalog:
            return UUID(catalog[0]["id"])
    except Exception as exc:
        logger.warning(
            "thread_product_catalog_fallback_failed",
            merchant_id=str(merchant.merchant_id),
            error=str(exc),
        )
    return None


def _build_buy_link(merchant: BotMerchantContext, product_id: UUID | None) -> str:
    username = merchant.bot_username or "this_bot"
    payload = f"buy_{product_id}" if product_id else "buy"
    return f"https://t.me/{username}?start={payload}"


def register(router: Router) -> None:
    @router.message(F.chat.type.in_({"supergroup", "group"}), F.forward_from_chat)
    async def on_thread_root_forward(
        message: Message, merchant: BotMerchantContext
    ) -> None:
        """Capture channel auto-forwards into the discussion group and save
        the thread_id → product_id mapping for later resolution."""
        fwd = _extract_channel_forward(message)
        if fwd is None:
            return
        channel_id, channel_message_id = fwd
        if merchant.channel_id and channel_id != merchant.channel_id:
            return
        try:
            product_id = await CoreClient().get_product_for_channel_message(
                merchant.merchant_id, channel_id, channel_message_id
            )
        except Exception as exc:
            logger.warning(
                "thread_root_lookup_failed",
                merchant_id=str(merchant.merchant_id),
                error=str(exc),
            )
            return
        if product_id is None:
            return
        try:
            redis = await get_redis()
            await redis.set(
                _thread_map_key(merchant.merchant_id, message.chat.id, message.message_id),
                str(product_id),
                ex=_THREAD_MAP_TTL,
            )
        except Exception as exc:
            logger.warning(
                "thread_root_map_failed",
                merchant_id=str(merchant.merchant_id),
                error=str(exc),
            )

    @router.message(F.chat.type.in_({"supergroup", "group"}), F.reply_to_message)
    async def on_discussion_reply(
        message: Message, merchant: BotMerchantContext
    ) -> None:
        if not merchant.ai_auto_reply_comments:
            return
        if not (message.text or message.caption):
            return
        if message.from_user is None:
            return

        text = (message.text or message.caption or "").strip()
        product_id = await _resolve_product_for_thread(message, merchant)

        # === Buy intent → redirect to DM, never share bank info in public ===
        if _customer_shows_buy_intent(text):
            link = _build_buy_link(merchant, product_id)
            await message.reply(
                "Great — let's keep your payment details private. "
                f"Tap here to continue in our private chat 👉 {link}",
                disable_web_page_preview=True,
            )
            logger.info(
                "buy_intent_redirected_to_dm",
                merchant_id=str(merchant.merchant_id),
                product_id=str(product_id) if product_id else None,
            )
            return

        # === Otherwise: AI answers product questions ===
        if not merchant.ai_provider or not merchant.ai_api_key:
            return

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
            customer_message=text,
            product_ctx=product_ctx,
            surface="COMMENT",
            catalog=catalog,
        )
        await message.reply(reply)
