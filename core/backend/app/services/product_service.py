import secrets
from uuid import UUID

import httpx
import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.product import Product
from app.repositories.inventory_repository import InventoryRepository
from app.repositories.product_repository import ProductRepository
from app.repositories.telegram_channel_repository import TelegramChannelRepository
from app.repositories.telegram_repository import TelegramBotConfigRepository
from app.schemas.product import ProductCreate, ProductUpdate

logger = structlog.get_logger()


class ProductNotFoundError(Exception):
    pass


class ProductConflictError(Exception):
    pass


class ProductService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.products = ProductRepository(db)
        self.inventory = InventoryRepository(db)
        self.telegram = TelegramBotConfigRepository(db)

    async def list_products(
        self,
        merchant_id: UUID,
        *,
        limit: int = 100,
        offset: int = 0,
        search: str | None = None,
    ) -> list[tuple[Product, int, int]]:
        products = await self.products.list_by_merchant(
            merchant_id, limit=limit, offset=offset, search=search
        )
        result: list[tuple[Product, int, int]] = []
        for p in products:
            ledger = await self.inventory.get(p.id)
            qty = ledger.quantity if ledger else 0
            reserved = ledger.reserved_quantity if ledger else 0
            result.append((p, qty, reserved))
        return result

    async def get_product(
        self, product_id: UUID, merchant_id: UUID
    ) -> tuple[Product, int, int]:
        product = await self.products.get(product_id, merchant_id)
        if not product:
            raise ProductNotFoundError()
        ledger = await self.inventory.get(product.id)
        return (
            product,
            (ledger.quantity if ledger else 0),
            (ledger.reserved_quantity if ledger else 0),
        )

    async def create(
        self, merchant_id: UUID, payload: ProductCreate
    ) -> tuple[Product, int, int, bool]:
        sku = (payload.sku or "").strip() or None
        if sku:
            if await self.products.get_by_sku(merchant_id, sku):
                raise ProductConflictError("sku_already_used")
        else:
            sku = f"AUTO-{secrets.token_hex(4).upper()}"

        product = await self.products.create(
            merchant_id=merchant_id,
            title=payload.title,
            description=payload.description,
            base_price=payload.base_price,
            sku=sku,
            image_urls=payload.image_urls,
            identifier=(payload.identifier or "").strip() or None,
            instructions=(payload.instructions or "").strip() or None,
        )
        await self.inventory.create(
            merchant_id=merchant_id,
            product_id=product.id,
            quantity=payload.initial_stock,
        )

        published = False
        if payload.publish_to_channel:
            cfg = await self.telegram.get_by_merchant(merchant_id)
            if cfg and cfg.channel_id:
                published = await self._publish_to_channel(
                    merchant_id=merchant_id,
                    product=product,
                )
                if published:
                    await self._mark_published(product, True)

        # Optional vision auto-identification. The Telegram svc PATCHes the
        # `identifier` back when done — async; we don't block creation.
        if payload.run_ocr and product.image_urls:
            try:
                await self.run_ocr_identification(product.id, merchant_id)
            except Exception as exc:
                logger.warning(
                    "ocr_kickoff_failed",
                    product_id=str(product.id),
                    error=repr(exc),
                )
        return product, payload.initial_stock, 0, published

    async def update(
        self, product_id: UUID, merchant_id: UUID, payload: ProductUpdate
    ) -> tuple[Product, int, int]:
        product = await self.products.get(product_id, merchant_id)
        if not product:
            raise ProductNotFoundError()
        if payload.sku and payload.sku != product.sku:
            other = await self.products.get_by_sku(merchant_id, payload.sku)
            if other:
                raise ProductConflictError("sku_already_used")
        updated = await self.products.update(
            product,
            title=payload.title,
            description=payload.description,
            base_price=payload.base_price,
            sku=payload.sku,
            image_urls=payload.image_urls,
            identifier=payload.identifier,
            instructions=payload.instructions,
        )
        if updated.is_published_to_channel:
            await self._mark_published(updated, False)
        ledger = await self.inventory.get(updated.id)
        return (
            updated,
            (ledger.quantity if ledger else 0),
            (ledger.reserved_quantity if ledger else 0),
        )

    async def delete(self, product_id: UUID, merchant_id: UUID) -> dict:
        product = await self.products.get(product_id, merchant_id)
        if not product:
            raise ProductNotFoundError()

        channel_repo = TelegramChannelRepository(self.db)
        posts = await channel_repo.list_by_product(product.id)
        result = {
            "channel_messages_total": len(posts),
            "channel_messages_deleted": 0,
            "channel_messages_failed": 0,
            "channel_reason": None,
        }
        if posts:
            tg_result = await self._delete_channel_messages(merchant_id, posts)
            if tg_result is not None:
                deleted = tg_result.get("deleted") or []
                failed = tg_result.get("failed") or []
                result["channel_messages_deleted"] = len(deleted)
                result["channel_messages_failed"] = len(failed)
                if failed and isinstance(failed[0], dict):
                    result["channel_reason"] = _classify_delete_error(failed[0].get("error"))
                elif tg_result.get("reason"):
                    result["channel_reason"] = tg_result["reason"]
            await channel_repo.delete_posts(posts)

        ledger = await self.inventory.get(product.id)
        if ledger:
            await self.db.delete(ledger)
            await self.db.flush()
        await self.products.delete(product)
        return result

    async def run_ocr_identification(
        self, product_id: UUID, merchant_id: UUID
    ) -> bool:
        """Fire-and-forget call to Telegram svc to run vision on the product images.
        Telegram svc PATCHes back via /internal/products/{id}/ocr-result when done."""
        product = await self.products.get(product_id, merchant_id)
        if not product:
            raise ProductNotFoundError()
        if not product.image_urls:
            return False
        url = f"{settings.TELEGRAM_SERVICE_URL}/api/v1/telegram/internal/ocr-product"
        headers = {"X-Service-Token": settings.X_SERVICE_TOKEN}
        payload = {
            "merchant_id": str(merchant_id),
            "product_id": str(product.id),
            "image_urls": list(product.image_urls or []),
        }
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                await client.post(url, headers=headers, json=payload)
            return True
        except httpx.HTTPError as exc:
            logger.warning(
                "ocr_dispatch_failed",
                merchant_id=str(merchant_id),
                product_id=str(product.id),
                error=repr(exc),
            )
            return False

    async def set_ocr_result(
        self, product_id: UUID, merchant_id: UUID, identifier_text: str
    ) -> None:
        product = await self.products.get(product_id, merchant_id)
        if not product:
            raise ProductNotFoundError()
        await self.products.set_ocr_identified(product, identifier_text)

    async def publish_existing_to_channel(
        self, product_id: UUID, merchant_id: UUID
    ) -> bool:
        product = await self.products.get(product_id, merchant_id)
        if not product:
            raise ProductNotFoundError()
        cfg = await self.telegram.get_by_merchant(merchant_id)
        if not cfg or not cfg.channel_id:
            return False
        ok = await self._publish_to_channel(merchant_id=merchant_id, product=product)
        if ok:
            await self._mark_published(product, True)
        return ok

    async def _mark_published(self, product: Product, value: bool) -> None:
        product.is_published_to_channel = value
        await self.db.flush()
        await self.db.refresh(product)

    async def _publish_to_channel(
        self, *, merchant_id: UUID, product: Product
    ) -> bool:
        url = f"{settings.TELEGRAM_SERVICE_URL}/api/v1/telegram/internal/publish-product"
        headers = {"X-Service-Token": settings.X_SERVICE_TOKEN}
        payload = {
            "merchant_id": str(merchant_id),
            "product_id": str(product.id),
            "title": product.title,
            "description": product.description,
            "base_price": str(product.base_price)
            if product.base_price is not None
            else None,
            "image_urls": list(product.image_urls or []),
        }
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                resp = await client.post(url, headers=headers, json=payload)
                resp.raise_for_status()
            return True
        except httpx.HTTPError as exc:
            logger.warning(
                "telegram_publish_failed",
                merchant_id=str(merchant_id),
                product_id=str(product.id),
                error_type=type(exc).__name__,
                error=repr(exc),
            )
            return False

    async def _delete_channel_messages(
        self, merchant_id: UUID, posts: list
    ) -> dict | None:
        if not posts:
            return None
        url = f"{settings.TELEGRAM_SERVICE_URL}/api/v1/telegram/internal/delete-channel-messages"
        headers = {"X-Service-Token": settings.X_SERVICE_TOKEN}
        payload = {
            "merchant_id": str(merchant_id),
            "channel_id": posts[0].channel_id,
            "message_ids": [p.message_id for p in posts],
        }
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(url, headers=headers, json=payload)
                resp.raise_for_status()
                return resp.json()
        except httpx.HTTPError as exc:
            logger.warning(
                "telegram_delete_messages_failed",
                merchant_id=str(merchant_id),
                error_type=type(exc).__name__,
                error=repr(exc),
            )
            return None


def _classify_delete_error(err: str | None) -> str:
    if not err:
        return "unknown"
    low = err.lower()
    if "not enough rights" in low or "permission" in low or "right to" in low:
        return "missing_delete_permission"
    if "message to delete not found" in low or "not found" in low:
        return "already_gone"
    return "unknown"
