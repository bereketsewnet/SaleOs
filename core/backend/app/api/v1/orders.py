"""Admin-side orders router. Customer-facing order placement lives in
`public_catalog.py` (uses Telegram initData auth instead of JWT)."""
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.middleware.auth import get_current_user, require_admin
from app.models.user import User
from app.repositories.payment_account_repository import PaymentAccountRepository
from app.repositories.product_repository import ProductRepository
from app.schemas.order import (
    OrderItemPublic,
    OrderPublic,
    OrderStatusUpdate,
    PaymentAccountPublic,
    PaymentRejectionRequest,
)
from app.services.media_service import ReceiptStorage
from app.services.order_service import OrderNotFoundError, OrderService

router = APIRouter()


def _require_merchant(user: User) -> UUID:
    if not user.merchant_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="no_merchant_context")
    return user.merchant_id


async def _to_public(order, db: AsyncSession) -> OrderPublic:
    product_repo = ProductRepository(db)
    items: list[OrderItemPublic] = []
    for it in order.items:
        product = await product_repo.get(it.product_id, order.merchant_id)
        title = product.title if product else "(deleted product)"
        items.append(
            OrderItemPublic(
                product_id=it.product_id,
                title=title,
                quantity=it.quantity,
                unit_price=it.unit_price,
                line_total=Decimal(str(it.unit_price)) * Decimal(it.quantity),
            )
        )
    payment_account = None
    if order.payment_account_id:
        accts = await PaymentAccountRepository(db).list_by_merchant(order.merchant_id)
        match = next((a for a in accts if a.id == order.payment_account_id), None)
        if match:
            payment_account = PaymentAccountPublic(
                bank_name=match.bank_name,
                account_number=match.account_number,
                account_holder_name=match.account_holder_name,
                phone=match.phone,
            )
    proof_url: str | None = None
    if order.payment_proof_url:
        try:
            proof_url = ReceiptStorage().presigned_url(order.payment_proof_url)
        except Exception:
            proof_url = None
    return OrderPublic(
        id=order.id,
        merchant_id=order.merchant_id,
        channel_source=order.channel_source,
        order_status=order.order_status,
        total_amount=order.total_amount,
        customer_info=order.customer_info,
        notes=order.notes,
        payment_account=payment_account,
        items=items,
        dm_contacts=[],
        payment_proof_url=proof_url,
        payment_proof_uploaded_at=order.payment_proof_uploaded_at,
        payment_verified_at=order.payment_verified_at,
        payment_rejection_reason=order.payment_rejection_reason,
        created_at=order.created_at,
    )


@router.get("/", response_model=list[OrderPublic])
async def list_orders(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
    status_eq: str | None = Query(default=None),
    channel_eq: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> list[OrderPublic]:
    merchant_id = _require_merchant(user)
    orders = await OrderService(db).list_for_merchant(
        merchant_id,
        status_eq=status_eq,
        channel_eq=channel_eq,
        limit=limit,
        offset=offset,
    )
    return [await _to_public(o, db) for o in orders]


@router.get("/{order_id}", response_model=OrderPublic)
async def get_order(
    order_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> OrderPublic:
    merchant_id = _require_merchant(user)
    try:
        order = await OrderService(db).get_for_merchant(order_id, merchant_id)
    except OrderNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not_found") from exc
    return await _to_public(order, db)


@router.patch("/{order_id}/status", response_model=OrderPublic)
async def update_order_status(
    order_id: UUID,
    payload: OrderStatusUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_admin),
) -> OrderPublic:
    merchant_id = _require_merchant(user)
    try:
        await OrderService(db).update_status(order_id, merchant_id, payload.order_status)
    except OrderNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not_found") from exc
    full = await OrderService(db).get_for_merchant(order_id, merchant_id)
    return await _to_public(full, db)


@router.patch("/{order_id}/verify-payment", response_model=OrderPublic)
async def verify_payment(
    order_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_admin),
) -> OrderPublic:
    merchant_id = _require_merchant(user)
    try:
        await OrderService(db).verify_payment(
            merchant_id=merchant_id, order_id=order_id, admin_user_id=user.id
        )
    except OrderNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not_found") from exc
    full = await OrderService(db).get_for_merchant(order_id, merchant_id)
    return await _to_public(full, db)


@router.patch("/{order_id}/reject-payment", response_model=OrderPublic)
async def reject_payment(
    order_id: UUID,
    payload: PaymentRejectionRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_admin),
) -> OrderPublic:
    merchant_id = _require_merchant(user)
    try:
        await OrderService(db).reject_payment(
            merchant_id=merchant_id, order_id=order_id, reason=payload.reason
        )
    except OrderNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not_found") from exc
    full = await OrderService(db).get_for_merchant(order_id, merchant_id)
    return await _to_public(full, db)
