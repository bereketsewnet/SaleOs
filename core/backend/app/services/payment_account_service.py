from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.payment_account import MerchantPaymentAccount
from app.repositories.payment_account_repository import PaymentAccountRepository
from app.schemas.payment_account import PaymentAccountCreate, PaymentAccountUpdate


class PaymentAccountNotFoundError(Exception):
    pass


class PaymentAccountService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = PaymentAccountRepository(db)

    async def list_for_merchant(self, merchant_id: UUID) -> list[MerchantPaymentAccount]:
        return await self.repo.list_by_merchant(merchant_id)

    async def get_default(self, merchant_id: UUID) -> MerchantPaymentAccount | None:
        return await self.repo.get_default(merchant_id)

    async def create(
        self, merchant_id: UUID, payload: PaymentAccountCreate
    ) -> MerchantPaymentAccount:
        return await self.repo.create(
            merchant_id=merchant_id,
            bank_name=payload.bank_name,
            account_number=payload.account_number,
            account_holder_name=payload.account_holder_name,
            phone=payload.phone,
        )

    async def update(
        self, account_id: UUID, merchant_id: UUID, payload: PaymentAccountUpdate
    ) -> MerchantPaymentAccount:
        account = await self.repo.get(account_id, merchant_id)
        if not account:
            raise PaymentAccountNotFoundError()
        return await self.repo.update(
            account,
            bank_name=payload.bank_name,
            account_number=payload.account_number,
            account_holder_name=payload.account_holder_name,
            phone=payload.phone,
            is_active=payload.is_active,
        )

    async def delete(self, account_id: UUID, merchant_id: UUID) -> None:
        account = await self.repo.get(account_id, merchant_id)
        if not account:
            raise PaymentAccountNotFoundError()
        await self.repo.delete(account)
