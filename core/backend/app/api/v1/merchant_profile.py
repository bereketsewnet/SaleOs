"""Editable merchant identity (business_name + contact info).
Any change triggers a bot reload so the AI agent + Mini App pick up the new info."""
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.middleware.auth import get_current_user, require_admin
from app.models.user import User
from app.repositories.merchant_repository import MerchantRepository
from app.schemas.merchant_profile import MerchantProfilePublic, MerchantProfileUpdate
from app.services.telegram_bot_service import TelegramBotService

router = APIRouter()


def _require_merchant(user: User):
    if not user.merchant_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="no_merchant_context")
    return user.merchant_id


@router.get("/", response_model=MerchantProfilePublic)
async def get_profile(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> MerchantProfilePublic:
    merchant_id = _require_merchant(user)
    merchant = await MerchantRepository(db).get_by_id(merchant_id)
    if not merchant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not_found")
    return MerchantProfilePublic.model_validate(merchant)


@router.patch("/", response_model=MerchantProfilePublic)
async def update_profile(
    payload: MerchantProfileUpdate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_admin),
) -> MerchantProfilePublic:
    merchant_id = _require_merchant(user)
    repo = MerchantRepository(db)
    merchant = await repo.get_by_id(merchant_id)
    if not merchant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not_found")

    # Conflict checks (email + phone are UNIQUE across all merchants)
    new_email = payload.contact_email
    if new_email and new_email != merchant.contact_email:
        existing = await repo.get_by_email(new_email)
        if existing and existing.id != merchant_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="email_already_used"
            )
    new_phone = payload.contact_phone
    if new_phone and new_phone != merchant.contact_phone:
        existing = await repo.get_by_phone(new_phone)
        if existing and existing.id != merchant_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="phone_already_used"
            )

    updated = await repo.update_profile(
        merchant,
        business_name=(payload.business_name.strip() if payload.business_name else None),
        contact_email=new_email,
        contact_phone=new_phone,
    )

    # Reload the bot so BotMerchantContext.business_name and downstream prompts refresh.
    background_tasks.add_task(TelegramBotService.notify_telegram_service, merchant_id)

    return MerchantProfilePublic.model_validate(updated)
