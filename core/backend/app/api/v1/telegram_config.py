from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.middleware.auth import get_current_user, require_admin
from app.models.user import User
from app.schemas.telegram_ai import (
    TelegramAISettingsPublic,
    TelegramAISettingsUpdate,
)
from app.schemas.telegram_config import (
    BUSINESS_TYPE_PRESETS,
    TelegramBotConfigPublic,
    TelegramBotConfigUpsert,
    TelegramBrandVoiceUpdate,
)
from app.services.telegram_bot_service import (
    TelegramBotService,
    TelegramTokenInvalidError,
)

router = APIRouter()


def _require_merchant(user: User) -> UUID:
    if not user.merchant_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="no_merchant_context")
    return user.merchant_id


@router.get("/", response_model=TelegramBotConfigPublic | None)
async def get_bot_config(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> TelegramBotConfigPublic | None:
    merchant_id = _require_merchant(user)
    config = await TelegramBotService(db).get_for_merchant(merchant_id)
    return TelegramBotConfigPublic.model_validate(config) if config else None


@router.put("/", response_model=TelegramBotConfigPublic)
async def upsert_bot_config(
    payload: TelegramBotConfigUpsert,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_admin),
) -> TelegramBotConfigPublic:
    merchant_id = _require_merchant(user)
    try:
        config = await TelegramBotService(db).upsert(merchant_id, payload)
    except TelegramTokenInvalidError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    background_tasks.add_task(TelegramBotService.notify_telegram_service, merchant_id)
    return TelegramBotConfigPublic.model_validate(config)


@router.patch("/brand-voice", response_model=TelegramBotConfigPublic)
async def update_brand_voice(
    payload: TelegramBrandVoiceUpdate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_admin),
) -> TelegramBotConfigPublic:
    merchant_id = _require_merchant(user)
    updated = await TelegramBotService(db).update_brand_voice(merchant_id, payload)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="connect_bot_first",
        )
    background_tasks.add_task(TelegramBotService.notify_telegram_service, merchant_id)
    return TelegramBotConfigPublic.model_validate(updated)


@router.get("/presets", response_model=dict)
async def get_presets(_: User = Depends(get_current_user)) -> dict:
    return {"business_types": BUSINESS_TYPE_PRESETS}


@router.get("/ai", response_model=TelegramAISettingsPublic | None)
async def get_ai_settings(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> TelegramAISettingsPublic | None:
    merchant_id = _require_merchant(user)
    return await TelegramBotService(db).get_ai_settings(merchant_id)


@router.patch("/ai", response_model=TelegramAISettingsPublic)
async def update_ai_settings(
    payload: TelegramAISettingsUpdate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_admin),
) -> TelegramAISettingsPublic:
    merchant_id = _require_merchant(user)
    result = await TelegramBotService(db).update_ai_settings(merchant_id, payload)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="connect_bot_first",
        )
    # Reload bot so the new key + toggles take effect immediately.
    background_tasks.add_task(TelegramBotService.notify_telegram_service, merchant_id)
    return result


@router.delete("/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_bot_config(
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_admin),
) -> None:
    merchant_id = _require_merchant(user)
    removed = await TelegramBotService(db).delete(merchant_id)
    if removed:
        background_tasks.add_task(TelegramBotService.notify_telegram_service, merchant_id)
