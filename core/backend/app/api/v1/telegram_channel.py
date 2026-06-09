from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.middleware.auth import get_current_user, require_admin
from app.models.user import User
from app.repositories.telegram_channel_repository import TelegramChannelRepository
from app.repositories.telegram_repository import TelegramBotConfigRepository
from app.schemas.telegram_channel import (
    TelegramChannelPostPublic,
    TelegramChannelStatus,
)

router = APIRouter()


def _require_merchant(user: User) -> UUID:
    if not user.merchant_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="no_merchant_context")
    return user.merchant_id


@router.get("/status", response_model=TelegramChannelStatus)
async def channel_status(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> TelegramChannelStatus:
    merchant_id = _require_merchant(user)
    config = await TelegramBotConfigRepository(db).get_by_merchant(merchant_id)
    if not config or not config.channel_id:
        return TelegramChannelStatus(connected=False)
    return TelegramChannelStatus(
        connected=True,
        channel_id=config.channel_id,
        channel_username=config.channel_username,
        channel_title=config.channel_title,
    )


@router.delete("/unbind", status_code=status.HTTP_204_NO_CONTENT)
async def channel_unbind(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_admin),
) -> None:
    merchant_id = _require_merchant(user)
    config = await TelegramBotConfigRepository(db).get_by_merchant(merchant_id)
    if config and config.channel_id:
        await TelegramChannelRepository(db).unbind_channel(config)


@router.get("/posts", response_model=list[TelegramChannelPostPublic])
async def list_channel_posts(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
    limit: int = 50,
    offset: int = 0,
) -> list[TelegramChannelPostPublic]:
    merchant_id = _require_merchant(user)
    posts = await TelegramChannelRepository(db).list_for_merchant(
        merchant_id, limit=limit, offset=offset
    )
    return [TelegramChannelPostPublic.model_validate(p) for p in posts]
