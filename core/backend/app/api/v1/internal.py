import secrets
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, Header, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import verify_service_token
from app.repositories.inventory_repository import InventoryRepository
from app.repositories.merchant_repository import MerchantRepository
from app.repositories.product_repository import ProductRepository
from app.repositories.telegram_channel_repository import TelegramChannelRepository
from app.repositories.telegram_repository import TelegramBotConfigRepository
from app.repositories.telegram_dm_contact_repository import TelegramDMContactRepository
from app.schemas.internal_product_import import ChannelPostProductImport
from app.schemas.product import OCRResult, ProductAgentContext, ProductPublic, UploadedImage
from app.schemas.telegram_channel import (
    TelegramChannelBind,
    TelegramChannelPostIngest,
    TelegramChannelPostPublic,
)
from app.schemas.telegram_config import TelegramBotConfigInternal
from app.services.media_service import MediaService
from app.services.product_service import ProductNotFoundError, ProductService
from app.services.telegram_bot_service import TelegramBotService
from app.utils.crypto import decrypt_secret

router = APIRouter()


def _require_service_token(x_service_token: str = Header(...)) -> None:
    if not verify_service_token(x_service_token):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid service token")


@router.post("/alert")
async def broadcast_alert(_: None = Depends(_require_service_token)) -> dict:
    """Phase 7 — admin WS broadcast."""
    raise NotImplementedError


@router.get("/health")
async def internal_health(_: None = Depends(_require_service_token)) -> dict:
    return {"status": "ok"}


@router.get(
    "/telegram-config/{merchant_id}",
    response_model=TelegramBotConfigInternal,
)
async def get_telegram_config_internal(
    merchant_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(_require_service_token),
) -> TelegramBotConfigInternal:
    data = await TelegramBotService(db).get_internal(merchant_id)
    if not data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not_found")
    return TelegramBotConfigInternal(**data)


@router.get(
    "/telegram-configs",
    response_model=list[TelegramBotConfigInternal],
)
async def list_telegram_configs_internal(
    db: AsyncSession = Depends(get_db),
    _: None = Depends(_require_service_token),
) -> list[TelegramBotConfigInternal]:
    configs = await TelegramBotConfigRepository(db).list_active()
    # Re-use TelegramBotService.get_internal so payment_accounts + dm_contacts +
    # defaults stay in sync between single-merchant and bulk responses.
    svc = TelegramBotService(db)
    out: list[TelegramBotConfigInternal] = []
    for c in configs:
        data = await svc.get_internal(c.merchant_id)
        if data:
            out.append(TelegramBotConfigInternal(**data))
    return out


@router.post(
    "/telegram-channel/{merchant_id}/bind",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def bind_telegram_channel(
    merchant_id: UUID,
    payload: TelegramChannelBind,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(_require_service_token),
) -> None:
    """Called by Telegram svc when the bot is promoted as admin of a channel."""
    config = await TelegramBotConfigRepository(db).get_by_merchant(merchant_id)
    if not config:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="config_not_found")
    await TelegramChannelRepository(db).bind_channel(
        config,
        channel_id=payload.channel_id,
        channel_username=payload.channel_username,
        channel_title=payload.channel_title,
    )


@router.post(
    "/telegram-channel/{merchant_id}/posts",
    response_model=TelegramChannelPostPublic,
)
async def ingest_telegram_channel_post(
    merchant_id: UUID,
    payload: TelegramChannelPostIngest,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(_require_service_token),
) -> TelegramChannelPostPublic:
    """Race-safe upsert: handler's passive call (posted_by_admin=False) won't
    overwrite a publish-from-admin row already marked True/linked."""
    repo = TelegramChannelRepository(db)
    post = await repo.upsert_post(
        merchant_id=merchant_id,
        channel_id=payload.channel_id,
        message_id=payload.message_id,
        caption=payload.caption,
        photo_file_id=payload.photo_file_id,
        posted_by_admin=payload.posted_by_admin,
        product_id=payload.product_id,
    )
    return TelegramChannelPostPublic.model_validate(post)


@router.post("/products/upload-image", response_model=UploadedImage)
async def internal_upload_image(
    merchant_id: UUID = Form(...),
    file: UploadFile = File(...),
    _: None = Depends(_require_service_token),
) -> UploadedImage:
    """Service-token-protected upload (used by the Telegram svc when ingesting
    a #product manual post — there's no JWT in that flow)."""
    if not file.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="missing_filename")
    data = await file.read()
    if len(data) > 10 * 1024 * 1024:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="too_large")
    try:
        result = MediaService().upload_product_image(
            merchant_id=merchant_id, data=data, filename=file.filename
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return UploadedImage(**result)


@router.post("/products/from-channel-post", response_model=ProductPublic)
async def import_product_from_channel_post(
    payload: ChannelPostProductImport,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(_require_service_token),
) -> ProductPublic:
    """Create a product from a parsed manual channel post + uploaded images.
    Links every related message_id to this product so delete + de-dupe work."""
    product_repo = ProductRepository(db)
    sku = f"TG-{secrets.token_hex(4).upper()}"
    product = await product_repo.create(
        merchant_id=payload.merchant_id,
        title=payload.title,
        description=payload.description,
        base_price=payload.base_price,
        sku=sku,
        image_urls=payload.image_urls,
    )
    # Imported from a manual post — already on the channel.
    product.is_published_to_channel = True
    await db.flush()
    await InventoryRepository(db).create(
        merchant_id=payload.merchant_id,
        product_id=product.id,
        quantity=0,
    )
    # Channel-post is already in DB (handler captured it earlier).
    # Link the primary + every related message to this product.
    channel_repo = TelegramChannelRepository(db)
    all_message_ids = [payload.primary_message_id, *payload.related_message_ids]
    for mid in all_message_ids:
        existing = await channel_repo.find_existing_post(payload.channel_id, mid)
        if existing and not existing.product_id:
            existing.product_id = product.id
    await db.flush()

    return ProductPublic(
        id=product.id,
        merchant_id=product.merchant_id,
        title=product.title,
        description=product.description,
        base_price=product.base_price,
        sku=product.sku,
        image_urls=list(product.image_urls or []),
        quantity=0,
        reserved_quantity=0,
        # Manual #product posts are already on the channel — mark as published.
        is_published_to_channel=True,
        identifier=product.identifier,
        instructions=product.instructions,
        is_ocr_identified=product.is_ocr_identified,
        created_at=product.created_at,
    )


# ---------- Agent-side endpoints (Telegram svc only) ----------


@router.get(
    "/products/{product_id}/agent-context",
    response_model=ProductAgentContext,
)
async def get_product_agent_context(
    product_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(_require_service_token),
) -> ProductAgentContext:
    """Effective per-product context with fallback to telegram_bot_configs defaults."""
    product_repo = ProductRepository(db)
    # Manually look up cross-merchant since svc-token has access to any.
    from sqlalchemy import select
    from app.models.product import Product

    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not_found")
    cfg = await TelegramBotConfigRepository(db).get_by_merchant(product.merchant_id)
    identifier_effective = product.identifier or (
        cfg.default_product_identifier if cfg else None
    )
    instructions_effective = product.instructions or (
        cfg.default_product_instructions if cfg else None
    )
    return ProductAgentContext(
        product_id=product.id,
        merchant_id=product.merchant_id,
        title=product.title,
        description=product.description,
        base_price=product.base_price,
        image_urls=list(product.image_urls or []),
        identifier_effective=identifier_effective,
        instructions_effective=instructions_effective,
        is_ocr_identified=product.is_ocr_identified,
    )


@router.patch(
    "/products/{product_id}/ocr-result",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def write_ocr_result(
    product_id: UUID,
    payload: OCRResult,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(_require_service_token),
) -> None:
    from sqlalchemy import select
    from app.models.product import Product

    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not_found")
    await ProductService(db).set_ocr_result(
        product_id, product.merchant_id, payload.identifier.strip()
    )


@router.get("/telegram-dm-contacts/{merchant_id}")
async def list_dm_contacts_internal(
    merchant_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(_require_service_token),
) -> list[dict]:
    contacts = await TelegramDMContactRepository(db).list_active(merchant_id)
    return [
        {
            "id": str(c.id),
            "kind": c.kind,
            "value": c.value,
            "label": c.label,
            "position": c.position,
        }
        for c in contacts
    ]


@router.get("/telegram-channel/{merchant_id}/product-by-message")
async def get_product_for_channel_message(
    merchant_id: UUID,
    channel_id: int,
    message_id: int,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(_require_service_token),
) -> dict:
    post = await TelegramChannelRepository(db).find_existing_post(channel_id, message_id)
    if not post or post.merchant_id != merchant_id:
        return {"product_id": None}
    return {"product_id": str(post.product_id) if post.product_id else None}


@router.get("/merchants/{merchant_id}/catalog")
async def get_merchant_catalog(
    merchant_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(_require_service_token),
    limit: int = 30,
) -> list[dict]:
    """Compact product list the AI reply agent uses to cross-sell + provide deep links.
    Effective identifier (per-product OR default) is included so the agent has context."""
    products = await ProductRepository(db).list_by_merchant(
        merchant_id, limit=limit
    )
    cfg = await TelegramBotConfigRepository(db).get_by_merchant(merchant_id)
    default_id = cfg.default_product_identifier if cfg else None
    return [
        {
            "id": str(p.id),
            "title": p.title,
            "description": p.description,
            "base_price": str(p.base_price) if p.base_price is not None else None,
            "image_url": (p.image_urls[0] if p.image_urls else None),
            "identifier_effective": p.identifier or default_id,
        }
        for p in products
    ]
