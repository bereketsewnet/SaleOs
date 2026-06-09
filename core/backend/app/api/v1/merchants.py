from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.middleware.auth import get_current_user, require_super_admin
from app.models.user import User, UserRole
from app.schemas.merchant import MerchantCreate, MerchantPublic
from app.services.merchant_service import (
    MerchantConflictError,
    MerchantNotFoundError,
    MerchantService,
)

router = APIRouter()


@router.get("/", response_model=list[MerchantPublic])
async def list_merchants(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_super_admin),
    limit: int = 100,
    offset: int = 0,
) -> list[MerchantPublic]:
    merchants = await MerchantService(db).list_all(limit=limit, offset=offset)
    return [MerchantPublic.model_validate(m) for m in merchants]


@router.post("/", response_model=MerchantPublic, status_code=status.HTTP_201_CREATED)
async def create_merchant(
    payload: MerchantCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_super_admin),
) -> MerchantPublic:
    try:
        merchant = await MerchantService(db).create(payload)
    except MerchantConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return MerchantPublic.model_validate(merchant)


@router.get("/{merchant_id}", response_model=MerchantPublic)
async def get_merchant(
    merchant_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> MerchantPublic:
    if user.role != UserRole.SUPER_ADMIN and user.merchant_id != merchant_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="forbidden")
    try:
        merchant = await MerchantService(db).get(merchant_id)
    except MerchantNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="merchant_not_found") from exc
    return MerchantPublic.model_validate(merchant)
