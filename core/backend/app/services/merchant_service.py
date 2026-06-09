from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.merchant import Merchant
from app.repositories.merchant_repository import MerchantRepository
from app.schemas.merchant import MerchantCreate


class MerchantNotFoundError(Exception):
    pass


class MerchantConflictError(Exception):
    pass


class MerchantService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.merchants = MerchantRepository(db)

    async def get(self, merchant_id: UUID) -> Merchant:
        merchant = await self.merchants.get_by_id(merchant_id)
        if not merchant:
            raise MerchantNotFoundError()
        return merchant

    async def list_all(self, limit: int = 100, offset: int = 0) -> list[Merchant]:
        return await self.merchants.list_all(limit=limit, offset=offset)

    async def create(self, payload: MerchantCreate) -> Merchant:
        if await self.merchants.get_by_phone(payload.contact_phone):
            raise MerchantConflictError("phone_already_registered")
        if await self.merchants.get_by_email(payload.contact_email):
            raise MerchantConflictError("email_already_registered")
        return await self.merchants.create(
            business_name=payload.business_name,
            contact_phone=payload.contact_phone,
            contact_email=payload.contact_email,
        )
