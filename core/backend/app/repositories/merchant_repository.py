from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.merchant import Merchant


class MerchantRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(self, merchant_id: UUID) -> Merchant | None:
        result = await self.db.execute(select(Merchant).where(Merchant.id == merchant_id))
        return result.scalar_one_or_none()

    async def get_by_phone(self, phone: str) -> Merchant | None:
        result = await self.db.execute(select(Merchant).where(Merchant.contact_phone == phone))
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Merchant | None:
        result = await self.db.execute(select(Merchant).where(Merchant.contact_email == email))
        return result.scalar_one_or_none()

    async def list_all(self, limit: int = 100, offset: int = 0) -> list[Merchant]:
        result = await self.db.execute(
            select(Merchant).order_by(Merchant.created_at.desc()).limit(limit).offset(offset)
        )
        return list(result.scalars().all())

    async def create(
        self,
        *,
        business_name: str,
        contact_phone: str,
        contact_email: str,
    ) -> Merchant:
        merchant = Merchant(
            business_name=business_name,
            contact_phone=contact_phone,
            contact_email=contact_email,
        )
        self.db.add(merchant)
        await self.db.flush()
        await self.db.refresh(merchant)
        return merchant

    async def update_profile(
        self,
        merchant: Merchant,
        *,
        business_name: str | None = None,
        contact_email: str | None = None,
        contact_phone: str | None = None,
    ) -> Merchant:
        if business_name is not None:
            merchant.business_name = business_name
        if contact_email is not None:
            merchant.contact_email = contact_email
        if contact_phone is not None:
            merchant.contact_phone = contact_phone
        await self.db.flush()
        await self.db.refresh(merchant)
        return merchant

