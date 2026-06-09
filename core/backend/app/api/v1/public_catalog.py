"""Customer-facing endpoints used by the Telegram Mini App.
Auth: Telegram initData HMAC (or dev bypass in development).
Multi-tenant: every request is scoped to the merchant_id resolved from initData/query.
"""
import json
from decimal import Decimal
from uuid import UUID

import httpx
import structlog
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.redis import get_redis
from app.middleware.telegram_initdata import (
    TelegramCustomer,
    current_telegram_customer,
)
from app.repositories.inventory_repository import InventoryRepository
from app.repositories.merchant_repository import MerchantRepository
from app.repositories.payment_account_repository import PaymentAccountRepository
from app.repositories.product_repository import ProductRepository
from app.repositories.telegram_dm_contact_repository import (
    TelegramDMContactRepository,
)
from app.repositories.telegram_repository import TelegramBotConfigRepository
from app.schemas.order import OrderPublic, PlaceOrderRequest
from app.services.media_service import ReceiptStorage
from app.services.order_service import (
    OrderNotFoundError,
    OrderService,
    OutOfStockError,
    ProductMissingError,
)

logger = structlog.get_logger()
router = APIRouter()


# ---------- Catalog (read-only) ----------


class CatalogProduct(BaseModel):
    id: UUID
    title: str
    description: str | None
    base_price: Decimal | None
    image_url: str | None
    in_stock: int = 0


class CatalogProductDetail(CatalogProduct):
    image_urls: list[str] = Field(default_factory=list)


@router.get("/products", response_model=list[CatalogProduct])
async def list_catalog_products(
    customer: TelegramCustomer = Depends(current_telegram_customer),
    db: AsyncSession = Depends(get_db),
    search: str | None = Query(default=None, max_length=200),
    limit: int = Query(default=100, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> list[CatalogProduct]:
    products = await ProductRepository(db).list_by_merchant(
        customer.merchant_id, limit=limit, offset=offset, search=search
    )
    inv_repo = InventoryRepository(db)
    out: list[CatalogProduct] = []
    for p in products:
        ledger = await inv_repo.get(p.id)
        available = max(0, (ledger.quantity - ledger.reserved_quantity)) if ledger else 0
        out.append(
            CatalogProduct(
                id=p.id,
                title=p.title,
                description=p.description,
                base_price=p.base_price,
                image_url=(p.image_urls[0] if p.image_urls else None),
                in_stock=available,
            )
        )
    return out


@router.get("/products/{product_id}", response_model=CatalogProductDetail)
async def get_catalog_product(
    product_id: UUID,
    customer: TelegramCustomer = Depends(current_telegram_customer),
    db: AsyncSession = Depends(get_db),
) -> CatalogProductDetail:
    product = await ProductRepository(db).get(product_id, customer.merchant_id)
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not_found")
    ledger = await InventoryRepository(db).get(product.id)
    available = max(0, (ledger.quantity - ledger.reserved_quantity)) if ledger else 0
    image_urls = list(product.image_urls or [])
    return CatalogProductDetail(
        id=product.id,
        title=product.title,
        description=product.description,
        base_price=product.base_price,
        image_url=(image_urls[0] if image_urls else None),
        image_urls=image_urls,
        in_stock=available,
    )


# ---------- Merchant info (payment + DM contacts + business identity) ----------


class CatalogMerchantInfo(BaseModel):
    business_name: str
    business_description: str | None = None
    payment_accounts: list[dict] = Field(default_factory=list)
    dm_contacts: list[dict] = Field(default_factory=list)


@router.get("/merchant-info", response_model=CatalogMerchantInfo)
async def get_merchant_info(
    customer: TelegramCustomer = Depends(current_telegram_customer),
    db: AsyncSession = Depends(get_db),
) -> CatalogMerchantInfo:
    merchant = await MerchantRepository(db).get_by_id(customer.merchant_id)
    if not merchant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not_found")
    cfg = await TelegramBotConfigRepository(db).get_by_merchant(customer.merchant_id)
    accounts = await PaymentAccountRepository(db).list_by_merchant(customer.merchant_id)
    contacts = await TelegramDMContactRepository(db).list_active(customer.merchant_id)
    return CatalogMerchantInfo(
        business_name=merchant.business_name,
        business_description=(cfg.business_description if cfg else None),
        payment_accounts=[
            {
                "bank_name": a.bank_name,
                "account_number": a.account_number,
                "account_holder_name": a.account_holder_name,
                "phone": a.phone,
            }
            for a in accounts
            if a.is_active
        ],
        dm_contacts=[
            {
                "kind": c.kind,
                "value": c.value,
                "label": c.label,
                "position": c.position,
            }
            for c in contacts
        ],
    )


# ---------- Chat (proxy to Telegram svc reply_agent, with Redis history) ----------


class ChatRequest(BaseModel):
    product_id: UUID | None = None
    message: str = Field(..., min_length=1, max_length=2000)


class ChatMessage(BaseModel):
    role: str  # "customer" or "agent"
    content: str


class ChatResponse(BaseModel):
    reply: str
    history: list[ChatMessage]


def _history_key(merchant_id: UUID, telegram_user_id: int, product_id: UUID | None) -> str:
    pid = str(product_id) if product_id else "general"
    return f"tg:chat:{merchant_id}:{telegram_user_id}:{pid}"


_HISTORY_CAP = 20  # keep last 20 turns total
_HISTORY_TTL = 60 * 60 * 24 * 7  # 7 days


@router.get("/chat", response_model=list[ChatMessage])
async def get_chat_history(
    customer: TelegramCustomer = Depends(current_telegram_customer),
    product_id: UUID | None = Query(default=None),
) -> list[ChatMessage]:
    redis = await get_redis()
    raw = await redis.lrange(
        _history_key(customer.merchant_id, customer.telegram_user_id, product_id),
        0,
        -1,
    )
    out: list[ChatMessage] = []
    for entry in raw:
        try:
            data = json.loads(entry)
            out.append(ChatMessage(**data))
        except Exception:
            continue
    return out


@router.post("/chat", response_model=ChatResponse)
async def chat(
    payload: ChatRequest,
    customer: TelegramCustomer = Depends(current_telegram_customer),
) -> ChatResponse:
    redis = await get_redis()
    key = _history_key(customer.merchant_id, customer.telegram_user_id, payload.product_id)

    # Load short history.
    raw = await redis.lrange(key, 0, -1)
    history: list[dict] = []
    for entry in raw[-8:]:
        try:
            history.append(json.loads(entry))
        except Exception:
            continue

    # Call Telegram svc internal chat-reply.
    url = f"{settings.TELEGRAM_SERVICE_URL}/api/v1/telegram/internal/chat-reply"
    headers = {"X-Service-Token": settings.X_SERVICE_TOKEN}
    body = {
        "merchant_id": str(customer.merchant_id),
        "telegram_user_id": customer.telegram_user_id,
        "product_id": str(payload.product_id) if payload.product_id else None,
        "message": payload.message,
        "history": history,
    }
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(url, headers=headers, json=body)
            resp.raise_for_status()
            data = resp.json()
            reply = data.get("reply") or "Sorry, I couldn't reply just now."
    except httpx.HTTPError as exc:
        logger.warning("chat_proxy_failed", error=repr(exc))
        reply = "Sorry, I couldn't reply just now. Please try again."

    # Append user + agent turns; cap; refresh TTL.
    await redis.rpush(key, json.dumps({"role": "customer", "content": payload.message}))
    await redis.rpush(key, json.dumps({"role": "agent", "content": reply}))
    await redis.ltrim(key, -_HISTORY_CAP, -1)
    await redis.expire(key, _HISTORY_TTL)

    # Return full current history for UI.
    raw2 = await redis.lrange(key, 0, -1)
    full: list[ChatMessage] = []
    for entry in raw2:
        try:
            full.append(ChatMessage(**json.loads(entry)))
        except Exception:
            continue
    return ChatResponse(reply=reply, history=full)


# ---------- Order placement + read ----------


@router.post("/orders", response_model=OrderPublic, status_code=status.HTTP_201_CREATED)
async def place_order(
    payload: PlaceOrderRequest,
    customer: TelegramCustomer = Depends(current_telegram_customer),
    db: AsyncSession = Depends(get_db),
) -> OrderPublic:
    try:
        return await OrderService(db).place_order(
            merchant_id=customer.merchant_id,
            telegram_user_id=customer.telegram_user_id,
            items=payload.items,
            customer=payload.customer,
            notes=payload.notes,
        )
    except OutOfStockError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": "out_of_stock",
                "product_id": str(exc.product_id),
                "available": exc.available,
            },
        ) from exc
    except ProductMissingError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "product_not_found", "product_id": str(exc)},
        ) from exc


@router.get("/orders/{order_id}", response_model=OrderPublic)
async def get_my_order(
    order_id: UUID,
    customer: TelegramCustomer = Depends(current_telegram_customer),
    db: AsyncSession = Depends(get_db),
) -> OrderPublic:
    from app.api.v1.orders import _to_public  # reuse the renderer

    try:
        order = await OrderService(db).get_for_merchant(order_id, customer.merchant_id)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not_found") from exc
    # Authorize: only the placing customer can read their own order.
    info = order.customer_info or {}
    placed_by = info.get("telegram_user_id")
    if not customer.is_dev and placed_by != customer.telegram_user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="not_your_order")
    return await _to_public(order, db)


_RECEIPT_MAX_BYTES = 8 * 1024 * 1024  # 8 MB


@router.post("/orders/{order_id}/payment-proof", response_model=OrderPublic)
async def upload_payment_proof(
    order_id: UUID,
    file: UploadFile = File(...),
    customer: TelegramCustomer = Depends(current_telegram_customer),
    db: AsyncSession = Depends(get_db),
) -> OrderPublic:
    """Mini App receipt upload — moves order to PAYMENT_SUBMITTED, publishes WS alert."""
    from app.api.v1.orders import _to_public

    data = await file.read()
    if not data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="empty_file")
    if len(data) > _RECEIPT_MAX_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="receipt_too_large",
        )
    try:
        await OrderService(db).attach_payment_proof(
            merchant_id=customer.merchant_id,
            telegram_user_id=customer.telegram_user_id,
            order_id=order_id,
            file_bytes=data,
            filename=file.filename or "receipt.jpg",
            is_dev=customer.is_dev,
        )
    except OrderNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not_found") from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail=str(exc)
        ) from exc

    full = await OrderService(db).get_for_merchant(order_id, customer.merchant_id)
    return await _to_public(full, db)
