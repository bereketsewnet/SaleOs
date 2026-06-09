from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.payment_account import MerchantPaymentAccount


class PaymentAccountRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list_by_merchant(self, merchant_id: UUID) -> list[MerchantPaymentAccount]:
        result = await self.db.execute(
            select(MerchantPaymentAccount)
            .where(MerchantPaymentAccount.merchant_id == merchant_id)
            .order_by(MerchantPaymentAccount.created_at.asc())
        )
        return list(result.scalars().all())

    async def get(self, account_id: UUID, merchant_id: UUID) -> MerchantPaymentAccount | None:
        result = await self.db.execute(
            select(MerchantPaymentAccount).where(
                MerchantPaymentAccount.id == account_id,
                MerchantPaymentAccount.merchant_id == merchant_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_default(self, merchant_id: UUID) -> MerchantPaymentAccount | None:
        result = await self.db.execute(
            select(MerchantPaymentAccount)
            .where(
                MerchantPaymentAccount.merchant_id == merchant_id,
                MerchantPaymentAccount.is_active.is_(True),
            )
            .order_by(MerchantPaymentAccount.created_at.asc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def create(
        self,
        *,
        merchant_id: UUID,
        bank_name: str,
        account_number: str,
        account_holder_name: str,
        phone: str | None,
    ) -> MerchantPaymentAccount:
        account = MerchantPaymentAccount(
            merchant_id=merchant_id,
            bank_name=bank_name,
            account_number=account_number,
            account_holder_name=account_holder_name,
            phone=phone,
            is_active=True,
        )
        self.db.add(account)
        await self.db.flush()
        await self.db.refresh(account)
        return account

    async def update(self, account: MerchantPaymentAccount, **fields) -> MerchantPaymentAccount:
        for key, value in fields.items():
            if value is not None:
                setattr(account, key, value)
        await self.db.flush()
        await self.db.refresh(account)
        return account

    async def delete(self, account: MerchantPaymentAccount) -> None:
        await self.db.delete(account)
        await self.db.flush()
