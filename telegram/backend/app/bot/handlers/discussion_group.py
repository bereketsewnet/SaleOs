"""Discussion-group handlers:
- Channel auto-forwards into the discussion group → save a Redis mapping
  `tg:thread:{merchant}:{discussion_chat}:{thread_msg_id} → product_id` so any
  later comment under that thread can resolve to the right product even if it
  replies to the bot's message instead of the channel post directly.
- Text comments → reply_agent answers. If the customer's text shows buy intent
  (keywords) we set a Redis flag for (merchant, user, thread).
- Photo comments → if the buy-intent flag is set, forward the photo to Core
  which creates a draft Order tied to the product for that thread.
"""
import re
from io import BytesIO
from uuid import UUID

import structlog
from aiogram import Bot, F, Router
from aiogram.types import Message

from app.bot.context import BotMerchantContext
from app.bot.handlers.dm import _build_product_context
from app.core.redis import get_redis
from app.services.core_client import CoreClient
from app.services.reply_agent import generate_reply

logger = structlog.get_logger()


_BUY_INTENT_TTL = 60 * 30  # 30 min
_THREAD_MAP_TTL = 60 * 60 * 24 * 30  # 30 days
_PENDING_DETAILS_TTL = 60 * 60  # 1 hour to collect phone+address

# Loose Ethiopian phone matcher: +251 / 251 / 0 prefix, 9 or 7 mobile prefix.
# Accepts optional spaces/dashes between groups.
_PHONE_REGEX = re.compile(
    r"(?:\+?251|0)\s?[79]\d{2}[\s\-]?\d{3}[\s\-]?\d{3,4}"
)

# Keywords that signal the customer wants to buy. Matched case-insensitively
# against the customer's message (English + Amharic). Anything here triggers
# the buy-intent flag — independent of whether the AI happens to quote our
# bank number back.
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
    "ግዛ",      # buy
    "ልግዛ",     # let me buy
    "እፈልጋለሁ",  # I want
    "ስንት",     # how much
    "ዋጋ",      # price
    "ክፈል",     # pay
]


def _buy_intent_key(merchant_id: UUID, user_id: int, thread_id: int) -> str:
    return f"tg:buyintent:{merchant_id}:{user_id}:{thread_id}"


def _thread_map_key(merchant_id: UUID, discussion_chat_id: int, thread_msg_id: int) -> str:
    return f"tg:thread:{merchant_id}:{discussion_chat_id}:{thread_msg_id}"


def _pending_details_key(merchant_id: UUID, user_id: int, thread_id: int) -> str:
    return f"tg:pending_details:{merchant_id}:{user_id}:{thread_id}"


def _extract_phone(text: str) -> str | None:
    if not text:
        return None
    match = _PHONE_REGEX.search(text)
    if not match:
        return None
    digits = re.sub(r"[\s\-]", "", match.group(0))
    return digits


def _strip_phone(text: str, phone_raw: str) -> str:
    """Return `text` with the phone fragment removed, leaving the rest as address."""
    return re.sub(r"\s+", " ", text.replace(phone_raw, "")).strip(" ,—-:|")


def _customer_shows_buy_intent(text: str) -> bool:
    if not text:
        return False
    lo = text.lower()
    return any(kw in lo for kw in _BUY_INTENT_KEYWORDS)


def _detect_account_number_in_reply(reply_text: str, merchant: BotMerchantContext) -> bool:
    """Secondary signal: the AI's reply quoted one of our bank account numbers."""
    if not reply_text:
        return False
    for acct in merchant.payment_accounts or []:
        number = (acct.get("account_number") or "").strip()
        if not number:
            continue
        # Loose match — strip non-digits so spaces/dashes/commas don't break it.
        if re.sub(r"\D", "", reply_text).find(number) >= 0:
            return True
    return False


def _thread_id(message: Message) -> int | None:
    tid = getattr(message, "message_thread_id", None)
    if tid is None and message.reply_to_message is not None:
        tid = message.reply_to_message.message_id
    return tid


def _extract_channel_forward(message: Message) -> tuple[int, int] | None:
    """Return (channel_id, channel_message_id) if `message` is a forward
    from the merchant's channel."""
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
    """Resolve product for this comment. Try, in order:
    1. reply_to_message has forward_origin (customer replied directly to the channel post)
    2. Redis thread→product mapping populated when the channel auto-forwarded.
    """
    # (1) Reply chain.
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

    # (2) Redis thread map (populated by the auto-forward handler below).
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

    # (3) Last-resort fallback: most recent published product. Covers threads
    # that existed before this code was deployed (no Redis mapping yet) and
    # threads where the bot missed the channel auto-forward. Admin can re-assign
    # the product in the panel if this picks wrong.
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


def register(router: Router) -> None:
    @router.message(F.chat.type.in_({"supergroup", "group"}), F.forward_from_chat)
    async def on_thread_root_forward(
        message: Message, merchant: BotMerchantContext
    ) -> None:
        """Telegram auto-forwards every channel post into the linked discussion
        group as a new message. Save the mapping (discussion_chat, msg_id) →
        product_id so later comments in this thread can resolve the product
        even if they reply to the bot's text instead of this forward."""
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
            logger.info(
                "thread_root_mapped",
                merchant_id=str(merchant.merchant_id),
                discussion_chat=message.chat.id,
                thread_msg_id=message.message_id,
                product_id=str(product_id),
            )
        except Exception as exc:
            logger.warning(
                "thread_root_map_failed",
                merchant_id=str(merchant.merchant_id),
                error=str(exc),
            )

    @router.message(F.chat.type.in_({"supergroup", "group"}), F.photo)
    async def on_discussion_photo(
        message: Message, merchant: BotMerchantContext, bot: Bot
    ) -> None:
        if message.from_user is None:
            return
        thread_id = _thread_id(message)
        if thread_id is None:
            return

        redis = await get_redis()
        flag_key = _buy_intent_key(
            merchant.merchant_id, message.from_user.id, thread_id
        )
        flagged = await redis.get(flag_key)
        if not flagged:
            logger.debug(
                "discussion_photo_no_buy_intent",
                merchant_id=str(merchant.merchant_id),
                user_id=message.from_user.id,
                thread_id=thread_id,
            )
            return

        # The flag value is the product_id that was resolved at the time the
        # text comment arrived. Use it directly so we don't accidentally pick
        # a different product on the second pass.
        try:
            product_id = UUID(flagged)
        except Exception:
            logger.warning(
                "discussion_photo_bad_flag_value",
                merchant_id=str(merchant.merchant_id),
                flagged=str(flagged),
            )
            await redis.delete(flag_key)
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
                "discussion_receipt_download_failed",
                merchant_id=str(merchant.merchant_id),
                error=str(exc),
            )
            return

        full_name = (
            getattr(message.from_user, "full_name", None)
            or message.from_user.first_name
        )

        try:
            result = await CoreClient().create_order_from_channel_comment(
                merchant_id=merchant.merchant_id,
                product_id=product_id,
                telegram_user_id=message.from_user.id,
                customer_name=full_name,
                receipt_bytes=data,
                receipt_filename=f"comment-receipt-{message.message_id}.jpg",
            )
        except Exception as exc:
            logger.warning(
                "discussion_receipt_order_failed",
                merchant_id=str(merchant.merchant_id),
                product_id=str(product_id),
                error=str(exc),
            )
            await message.reply(
                "Thanks — we got the screenshot but something went wrong creating the order. Our team will contact you."
            )
            return

        await redis.delete(flag_key)
        order_id = result["order_id"]
        # Ask the customer to share phone + address so we can deliver.
        await redis.set(
            _pending_details_key(
                merchant.merchant_id, message.from_user.id, thread_id
            ),
            order_id,
            ex=_PENDING_DETAILS_TTL,
        )
        await message.reply(
            f"✅ Got your payment screenshot — order #{order_id[:8]} is created.\n\n"
            f"To finish, please reply here with your *phone number* and *delivery address*.\n"
            f"Example: `+251911223344 — Bole, Addis Ababa`",
            parse_mode="Markdown",
        )

    @router.message(F.chat.type.in_({"supergroup", "group"}), F.reply_to_message)
    async def on_discussion_reply(
        message: Message, merchant: BotMerchantContext
    ) -> None:
        if not (message.text or message.caption):
            return
        if message.from_user is None:
            return

        text = (message.text or message.caption or "").strip()
        thread_id = _thread_id(message)

        # === 1. Pending-details capture (after a receipt order was just created) ===
        if thread_id is not None:
            redis = await get_redis()
            pending_key = _pending_details_key(
                merchant.merchant_id, message.from_user.id, thread_id
            )
            pending_order_id = await redis.get(pending_key)
            if pending_order_id:
                phone = _extract_phone(text)
                if not phone:
                    await message.reply(
                        "I couldn't find a phone number in your reply. "
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
                        "pending_details_update_failed",
                        merchant_id=str(merchant.merchant_id),
                        error=str(exc),
                    )
                    await message.reply(
                        "Thanks — something went wrong saving your details. Our team will reach out."
                    )
                    return
                await redis.delete(pending_key)
                address_line = f"\nAddress: {address}" if address else ""
                await message.reply(
                    f"Got it ✓\nPhone: {phone}{address_line}\n\n"
                    f"We'll confirm your order shortly."
                )
                return

        # === 2. Normal AI reply for product questions ===
        if not merchant.ai_auto_reply_comments:
            return
        if not merchant.ai_provider or not merchant.ai_api_key:
            return

        product_id = await _resolve_product_for_thread(message, merchant)

        # Set the buy-intent flag based on the CUSTOMER's text — this is the
        # primary signal, before we even call the AI. Independent of what the
        # AI happens to quote back.
        customer_intent = _customer_shows_buy_intent(text)
        if customer_intent and product_id is not None and thread_id is not None:
            try:
                redis = await get_redis()
                await redis.set(
                    _buy_intent_key(
                        merchant.merchant_id, message.from_user.id, thread_id
                    ),
                    str(product_id),
                    ex=_BUY_INTENT_TTL,
                )
                logger.info(
                    "buy_intent_flag_set_from_customer",
                    merchant_id=str(merchant.merchant_id),
                    user_id=message.from_user.id,
                    thread_id=thread_id,
                    product_id=str(product_id),
                )
            except Exception as exc:
                logger.warning(
                    "buy_intent_flag_set_failed",
                    merchant_id=str(merchant.merchant_id),
                    error=str(exc),
                )

        # Generate AI reply.
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

        # Secondary signal: if customer text didn't match keywords but the AI
        # nonetheless quoted our bank account, treat that as buy intent too.
        if (
            not customer_intent
            and product_id is not None
            and thread_id is not None
            and _detect_account_number_in_reply(reply, merchant)
        ):
            try:
                redis = await get_redis()
                await redis.set(
                    _buy_intent_key(
                        merchant.merchant_id, message.from_user.id, thread_id
                    ),
                    str(product_id),
                    ex=_BUY_INTENT_TTL,
                )
                logger.info(
                    "buy_intent_flag_set_from_reply",
                    merchant_id=str(merchant.merchant_id),
                    thread_id=thread_id,
                    product_id=str(product_id),
                )
            except Exception as exc:
                logger.warning(
                    "buy_intent_flag_set_failed",
                    merchant_id=str(merchant.merchant_id),
                    error=str(exc),
                )
