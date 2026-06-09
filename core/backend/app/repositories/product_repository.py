from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product import Product


class ProductRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list_by_merchant(
        self,
        merchant_id: UUID,
        *,
        limit: int = 100,
        offset: int = 0,
        search: str | None = None,
    ) -> list[Product]:
        stmt = (
            select(Product)
            .where(Product.merchant_id == merchant_id)
            .order_by(Product.created_at.desc())
        )
        if search:
            like = f"%{search}%"
            stmt = stmt.where(Product.title.ilike(like))
        stmt = stmt.limit(limit).offset(offset)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get(self, product_id: UUID, merchant_id: UUID) -> Product | None:
        result = await self.db.execute(
            select(Product).where(
                Product.id == product_id,
                Product.merchant_id == merchant_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_by_sku(self, merchant_id: UUID, sku: str) -> Product | None:
        result = await self.db.execute(
            select(Product).where(
                Product.merchant_id == merchant_id,
                Product.sku == sku,
            )
        )
        return result.scalar_one_or_none()

    async def create(
        self,
        *,
        merchant_id: UUID,
        title: str,
        description: str | None,
        base_price: Decimal | None,
        sku: str | None,
        image_urls: list[str],
        identifier: str | None = None,
        instructions: str | None = None,
    ) -> Product:
        product = Product(
            merchant_id=merchant_id,
            title=title,
            description=description,
            base_price=base_price,
            sku=sku,
            image_urls=image_urls,
            identifier=identifier,
            instructions=instructions,
        )
        self.db.add(product)
        await self.db.flush()
        await self.db.refresh(product)
        return product

    async def set_ocr_identified(self, product: Product, identifier_text: str) -> Product:
        product.identifier = identifier_text
        product.is_ocr_identified = True
        await self.db.flush()
        await self.db.refresh(product)
        return product

    async def update(self, product: Product, **fields) -> Product:
        for k, v in fields.items():
            if v is not None:
                setattr(product, k, v)
        await self.db.flush()
        await self.db.refresh(product)
        return product

    async def delete(self, product: Product) -> None:
        await self.db.delete(product)
        await self.db.flush()
