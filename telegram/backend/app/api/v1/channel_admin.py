from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel

from app.core.config import settings
from app.services.bot_manager import get_bot_manager

logger = structlog.get_logger()
router = APIRouter()


def _require_service_token(x_service_token: str = Header(...)) -> None:
    if x_service_token != settings.X_SERVICE_TOKEN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid service token")


class DeleteChannelMessagesRequest(BaseModel):
    merchant_id: UUID
    channel_id: int
    message_ids: list[int]


@router.post("/internal/delete-channel-messages")
async def delete_channel_messages(
    payload: DeleteChannelMessagesRequest, _: None = Depends(_require_service_token)
) -> dict:
    bundle = get_bot_manager().get_bot_for_merchant(payload.merchant_id)
    if bundle is None:
        logger.warning(
            "delete_channel_messages_no_bot",
            merchant_id=str(payload.merchant_id),
        )
        return {"deleted": [], "skipped": payload.message_ids, "reason": "bot_not_running"}

    bot = bundle.bot
    deleted: list[int] = []
    failed: list[dict] = []
    for mid in payload.message_ids:
        try:
            await bot.delete_message(chat_id=payload.channel_id, message_id=mid)
            deleted.append(mid)
        except Exception as exc:
            err = str(exc)
            failed.append({"message_id": mid, "error": err})
            logger.warning(
                "delete_channel_message_failed",
                merchant_id=str(payload.merchant_id),
                channel_id=payload.channel_id,
                message_id=mid,
                error_type=type(exc).__name__,
                error=err,
            )
    return {"deleted": deleted, "failed": failed}
