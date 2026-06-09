from decimal import Decimal
from uuid import UUID

import structlog
from aiogram import Router
from aiogram.filters import CommandObject, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.bot.context import BotMerchantContext
from app.core.redis import get_redis
from app.services.core_client import CoreClient

logger = structlog.get_logger()


_DM_BUY_TTL = 60 * 60  # 1 hour


def dm_buy_key(merchant_id: UUID, user_id: int) -> str:
    """Customer arrived via `?start=buy_<product>`. Until they post a receipt
    here, we know they're in 'buy mode' for this product."""
    return f"tg:dm_buy:{merchant_id}:{user_id}"


def register(router: Router) -> None:
    @router.message(CommandStart(deep_link=True))
    async def handle_start_with_deep_link(
        message: Message,
        command: CommandObject,
        merchant: BotMerchantContext,
        state: FSMContext,
    ) -> None:
        """Customer arrived via t.me/{bot}?start=<payload>.
        Supported payloads:
          - product_<uuid> → remember product so the AI agent answers in context.
          - buy_<uuid>     → start the private buy flow (bank info + receipt request).
        """
        payload = (command.args or "").strip()
        product_id: UUID | None = None
        is_buy = False
        if payload.startswith("buy_"):
            is_buy = True
            try:
                product_id = UUID(payload[len("buy_") :])
            except ValueError:
                product_id = None
        elif payload.startswith("product_"):
            try:
                product_id = UUID(payload[len("product_") :])
            except ValueError:
                product_id = None

        if product_id:
            await state.update_data(current_product_id=str(product_id))
            logger.info(
                "start_deep_link",
                merchant_id=str(merchant.merchant_id),
                product_id=str(product_id),
                mode="buy" if is_buy else "product",
            )

        if is_buy and product_id and message.from_user is not None:
            await _start_buy_flow(message, merchant, product_id)
            return

        await _send_welcome(message, merchant)

    @router.message(CommandStart())
    async def handle_start(
        message: Message, merchant: BotMerchantContext, state: FSMContext
    ) -> None:
        await _send_welcome(message, merchant)


async def _start_buy_flow(
    message: Message, merchant: BotMerchantContext, product_id: UUID
) -> None:
    """DM the customer with bank info + ask for a payment screenshot.
    Sets a Redis flag so the next photo in this DM gets attached to an order.

    For SERVICE_INQUIRY merchants we skip the payment flow entirely and just
    say hello — the customer is here to discuss, not to pay upfront."""
    # Pre-flight: product must exist + have a price.
    title = "this offering"
    price_str = None
    try:
        ctx = await CoreClient().get_product_agent_context(product_id)
        if ctx:
            title = ctx.get("title") or title
            bp = ctx.get("base_price")
            if bp is not None:
                price_str = f"ETB {Decimal(str(bp))}"
    except Exception as exc:
        logger.warning(
            "buy_flow_product_lookup_failed",
            merchant_id=str(merchant.merchant_id),
            product_id=str(product_id),
            error=str(exc),
        )

    if merchant.business_mode == "SERVICE_INQUIRY":
        await message.answer(
            f"👋 Hi! Thanks for your interest in *{title}*.\n\n"
            f"Tell me a bit about what you're looking for and we'll take it from there.",
            parse_mode="Markdown",
        )
        return

    # Persist buy intent so the receipt handler picks the right product.
    try:
        redis = await get_redis()
        await redis.set(
            dm_buy_key(merchant.merchant_id, message.from_user.id),
            str(product_id),
            ex=_DM_BUY_TTL,
        )
    except Exception as exc:
        logger.warning(
            "buy_flow_flag_failed",
            merchant_id=str(merchant.merchant_id),
            error=str(exc),
        )

    parts: list[str] = []
    parts.append(f"👋 Hi! You're buying *{title}*" + (f" — {price_str}" if price_str else "") + ".")
    parts.append("")

    accts = merchant.payment_accounts or []
    if accts:
        parts.append("💳 *Send your payment to one of these accounts:*")
        for a in accts:
            bank = a.get("bank_name") or ""
            num = a.get("account_number") or ""
            holder = a.get("account_holder_name") or ""
            line = f"• {bank} — `{num}` — {holder}"
            if a.get("phone"):
                line += f" — {a['phone']}"
            parts.append(line)
        parts.append("")
    else:
        parts.append("⚠️ Our payment accounts aren't set up yet. Please ping our team.")
        parts.append("")

    parts.append("📸 *After paying, send the payment screenshot here* and I'll create your order.")
    parts.append("")
    parts.append("(All your payment details stay private in this chat.)")

    await message.answer("\n".join(parts), parse_mode="Markdown")


async def _send_welcome(message: Message, merchant: BotMerchantContext) -> None:
    customer_name = (message.from_user.first_name or "").strip() or "there"
    if merchant.welcome_message:
        await message.answer(merchant.welcome_message)
        return
    business = merchant.business_name or "us"
    parts = [f"👋 Hello {customer_name}!", ""]
    if merchant.business_description:
        parts.append(f"<b>{business}</b> — {merchant.business_description}")
    else:
        parts.append(f"You're now connected with <b>{business}</b>.")
    parts.append("")
    parts.append("Send me a message and I'll get back to you.")
    await message.answer("\n".join(parts), parse_mode="HTML")
