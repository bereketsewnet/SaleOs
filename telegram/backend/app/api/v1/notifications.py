"""Internal endpoint Core calls when an order status changes — DMs the customer
via the merchant's bot."""
from uuid import UUID

import structlog
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, Field

from app.core.config import settings
from app.services.bot_manager import get_bot_manager

logger = structlog.get_logger()
router = APIRouter()


def _require_service_token(x_service_token: str = Header(...)) -> None:
    if x_service_token != settings.X_SERVICE_TOKEN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid service token")


class DMCustomerRequest(BaseModel):
    merchant_id: UUID
    telegram_user_id: int
    message: str = Field(..., min_length=1, max_length=4000)


@router.post("/internal/dm-customer")
async def dm_customer(
    payload: DMCustomerRequest, _: None = Depends(_require_service_token)
) -> dict:
    bundle = get_bot_manager().get_bot_for_merchant(payload.merchant_id)
    if bundle is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="bot_not_running"
        )
    try:
        await bundle.bot.send_message(
            chat_id=payload.telegram_user_id,
            text=payload.message,
            parse_mode="Markdown",
            disable_web_page_preview=True,
        )
    except TelegramForbiddenError:
        # Customer hasn't started the bot or blocked it — not fatal, just log.
        logger.info(
            "dm_customer_forbidden",
            merchant_id=str(payload.merchant_id),
            telegram_user_id=payload.telegram_user_id,
        )
        return {"sent": False, "reason": "user_not_reachable"}
    except TelegramBadRequest as exc:
        logger.warning(
            "dm_customer_bad_request",
            merchant_id=str(payload.merchant_id),
            error=str(exc),
        )
        return {"sent": False, "reason": "bad_request"}
    return {"sent": True}
