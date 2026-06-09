from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.middleware.auth import get_current_user, require_admin
from app.models.user import User
from app.schemas.payment_account import (
    PaymentAccountCreate,
    PaymentAccountPublic,
    PaymentAccountUpdate,
)
from app.services.payment_account_service import (
    PaymentAccountNotFoundError,
    PaymentAccountService,
)

router = APIRouter()


def _require_merchant(user: User) -> UUID:
    if not user.merchant_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="no_merchant_context")
    return user.merchant_id


@router.get("/", response_model=list[PaymentAccountPublic])
async def list_payment_accounts(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[PaymentAccountPublic]:
    merchant_id = _require_merchant(user)
    accounts = await PaymentAccountService(db).list_for_merchant(merchant_id)
    return [PaymentAccountPublic.model_validate(a) for a in accounts]


@router.post("/", response_model=PaymentAccountPublic, status_code=status.HTTP_201_CREATED)
async def create_payment_account(
    payload: PaymentAccountCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_admin),
) -> PaymentAccountPublic:
    merchant_id = _require_merchant(user)
    account = await PaymentAccountService(db).create(merchant_id, payload)
    return PaymentAccountPublic.model_validate(account)


@router.patch("/{account_id}", response_model=PaymentAccountPublic)
async def update_payment_account(
    account_id: UUID,
    payload: PaymentAccountUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_admin),
) -> PaymentAccountPublic:
    merchant_id = _require_merchant(user)
    try:
        account = await PaymentAccountService(db).update(account_id, merchant_id, payload)
    except PaymentAccountNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not_found") from exc
    return PaymentAccountPublic.model_validate(account)


@router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_payment_account(
    account_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_admin),
) -> None:
    merchant_id = _require_merchant(user)
    try:
        await PaymentAccountService(db).delete(account_id, merchant_id)
    except PaymentAccountNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not_found") from exc
