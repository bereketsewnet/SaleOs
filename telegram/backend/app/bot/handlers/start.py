from uuid import UUID

import structlog
from aiogram import Router
from aiogram.filters import CommandObject, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.bot.context import BotMerchantContext

logger = structlog.get_logger()


def register(router: Router) -> None:
    @router.message(CommandStart(deep_link=True))
    async def handle_start_with_deep_link(
        message: Message,
        command: CommandObject,
        merchant: BotMerchantContext,
        state: FSMContext,
    ) -> None:
        """Customer arrived via t.me/{bot}?start=product_<id>.
        Remember the product so the DM agent answers in-context."""
        payload = command.args or ""
        product_id: UUID | None = None
        if payload.startswith("product_"):
            try:
                product_id = UUID(payload[len("product_") :])
            except ValueError:
                product_id = None

        if product_id:
            await state.update_data(current_product_id=str(product_id))
            logger.info(
                "start_deep_link_product",
                merchant_id=str(merchant.merchant_id),
                product_id=str(product_id),
            )

        await _send_welcome(message, merchant)

    @router.message(CommandStart())
    async def handle_start(
        message: Message, merchant: BotMerchantContext, state: FSMContext
    ) -> None:
        await _send_welcome(message, merchant)


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
