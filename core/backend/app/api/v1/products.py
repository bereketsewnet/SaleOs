from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Query,
    UploadFile,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.middleware.auth import get_current_user, require_admin
from app.models.product import Product
from app.models.user import User
from app.schemas.product import (
    ProductCreate,
    ProductPublic,
    ProductUpdate,
    UploadedImage,
)
from app.services.media_service import MediaService
from app.services.product_service import (
    ProductConflictError,
    ProductNotFoundError,
    ProductService,
)

router = APIRouter()


def _require_merchant(user: User) -> UUID:
    if not user.merchant_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="no_merchant_context")
    return user.merchant_id


def _to_public(product: Product, quantity: int, reserved: int) -> ProductPublic:
    return ProductPublic(
        id=product.id,
        merchant_id=product.merchant_id,
        title=product.title,
        description=product.description,
        base_price=product.base_price,
        sku=product.sku,
        image_urls=list(product.image_urls or []),
        quantity=quantity,
        reserved_quantity=reserved,
        is_published_to_channel=product.is_published_to_channel,
        identifier=product.identifier,
        instructions=product.instructions,
        is_ocr_identified=product.is_ocr_identified,
        created_at=product.created_at,
    )


@router.get("/", response_model=list[ProductPublic])
async def list_products(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
    search: str | None = Query(default=None, max_length=200),
    limit: int = Query(default=100, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> list[ProductPublic]:
    merchant_id = _require_merchant(user)
    rows = await ProductService(db).list_products(
        merchant_id, limit=limit, offset=offset, search=search
    )
    return [_to_public(p, q, r) for (p, q, r) in rows]


@router.post("/upload-image", response_model=UploadedImage)
async def upload_image(
    file: UploadFile = File(...),
    user: User = Depends(require_admin),
) -> UploadedImage:
    merchant_id = _require_merchant(user)
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


@router.get("/{product_id}", response_model=ProductPublic)
async def get_product(
    product_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ProductPublic:
    merchant_id = _require_merchant(user)
    try:
        p, q, r = await ProductService(db).get_product(product_id, merchant_id)
    except ProductNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not_found") from exc
    return _to_public(p, q, r)


@router.post("/", response_model=ProductPublic, status_code=status.HTTP_201_CREATED)
async def create_product(
    payload: ProductCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_admin),
) -> ProductPublic:
    merchant_id = _require_merchant(user)
    try:
        p, q, r, _published = await ProductService(db).create(merchant_id, payload)
    except ProductConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return _to_public(p, q, r)


@router.patch("/{product_id}", response_model=ProductPublic)
async def update_product(
    product_id: UUID,
    payload: ProductUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_admin),
) -> ProductPublic:
    merchant_id = _require_merchant(user)
    try:
        p, q, r = await ProductService(db).update(product_id, merchant_id, payload)
    except ProductNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not_found") from exc
    except ProductConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return _to_public(p, q, r)


@router.delete("/{product_id}")
async def delete_product(
    product_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_admin),
) -> dict:
    """Returns a summary so the UI can warn if the channel side could not be cleared."""
    merchant_id = _require_merchant(user)
    try:
        return await ProductService(db).delete(product_id, merchant_id)
    except ProductNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not_found") from exc


@router.post("/{product_id}/publish-to-channel")
async def publish_product_to_channel(
    product_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_admin),
) -> dict:
    merchant_id = _require_merchant(user)
    try:
        published = await ProductService(db).publish_existing_to_channel(product_id, merchant_id)
    except ProductNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not_found") from exc
    if not published:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="channel_not_connected_or_publish_failed",
        )
    return {"published": True}


@router.post("/{product_id}/run-ocr")
async def run_ocr(
    product_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_admin),
) -> dict:
    merchant_id = _require_merchant(user)
    try:
        dispatched = await ProductService(db).run_ocr_identification(product_id, merchant_id)
    except ProductNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not_found") from exc
    return {"dispatched": dispatched}
