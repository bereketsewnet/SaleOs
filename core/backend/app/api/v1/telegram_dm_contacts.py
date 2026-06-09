from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.middleware.auth import get_current_user, require_admin
from app.models.user import User
from app.schemas.telegram_dm_contact import (
    DMContactCreate,
    DMContactPublic,
    DMContactReorderItem,
    DMContactUpdate,
)
from app.services.telegram_bot_service import TelegramBotService
from app.services.telegram_dm_contact_service import (
    DMContactNotFoundError,
    TelegramDMContactService,
)

router = APIRouter()


def _require_merchant(user: User) -> UUID:
    if not user.merchant_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="no_merchant_context")
    return user.merchant_id


@router.get("/", response_model=list[DMContactPublic])
async def list_contacts(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[DMContactPublic]:
    merchant_id = _require_merchant(user)
    contacts = await TelegramDMContactService(db).list_for_merchant(merchant_id)
    return [DMContactPublic.model_validate(c) for c in contacts]


@router.post("/", response_model=DMContactPublic, status_code=status.HTTP_201_CREATED)
async def create_contact(
    payload: DMContactCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_admin),
) -> DMContactPublic:
    merchant_id = _require_merchant(user)
    contact = await TelegramDMContactService(db).create(merchant_id, payload)
    background_tasks.add_task(TelegramBotService.notify_telegram_service, merchant_id)
    return DMContactPublic.model_validate(contact)


@router.patch("/{contact_id}", response_model=DMContactPublic)
async def update_contact(
    contact_id: UUID,
    payload: DMContactUpdate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_admin),
) -> DMContactPublic:
    merchant_id = _require_merchant(user)
    try:
        contact = await TelegramDMContactService(db).update(contact_id, merchant_id, payload)
    except DMContactNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not_found") from exc
    background_tasks.add_task(TelegramBotService.notify_telegram_service, merchant_id)
    return DMContactPublic.model_validate(contact)


@router.delete("/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_contact(
    contact_id: UUID,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_admin),
) -> None:
    merchant_id = _require_merchant(user)
    try:
        await TelegramDMContactService(db).delete(contact_id, merchant_id)
    except DMContactNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not_found") from exc
    background_tasks.add_task(TelegramBotService.notify_telegram_service, merchant_id)


@router.post("/reorder", status_code=status.HTTP_204_NO_CONTENT)
async def reorder_contacts(
    items: list[DMContactReorderItem],
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_admin),
) -> None:
    merchant_id = _require_merchant(user)
    positions = {item.id: item.position for item in items}
    await TelegramDMContactService(db).reorder(merchant_id, positions)
    background_tasks.add_task(TelegramBotService.notify_telegram_service, merchant_id)
