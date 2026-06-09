from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel

from app.core.config import settings
from app.services.chat_service import generate_chat_reply

router = APIRouter()


def _require_service_token(x_service_token: str = Header(...)) -> None:
    if x_service_token != settings.X_SERVICE_TOKEN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid service token")


class ChatTurn(BaseModel):
    role: str  # "customer" or "agent"
    content: str


class ChatReplyRequest(BaseModel):
    merchant_id: UUID
    telegram_user_id: int
    product_id: UUID | None = None
    message: str
    history: list[ChatTurn] = []


@router.post("/internal/chat-reply")
async def chat_reply(
    payload: ChatReplyRequest, _: None = Depends(_require_service_token)
) -> dict:
    reply = await generate_chat_reply(
        merchant_id=payload.merchant_id,
        telegram_user_id=payload.telegram_user_id,
        product_id=payload.product_id,
        message=payload.message,
        history=[t.model_dump() for t in payload.history],
    )
    return {"reply": reply}
