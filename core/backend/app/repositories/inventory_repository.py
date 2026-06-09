from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.inventory import InventoryLedger


class InventoryRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get(self, product_id: UUID) -> InventoryLedger | None:
        result = await self.db.execute(
            select(InventoryLedger).where(InventoryLedger.product_id == product_id)
        )
        return result.scalar_one_or_none()

    async def get_for_update(self, product_id: UUID) -> InventoryLedger | None:
        """SELECT FOR UPDATE — used by order placement to prevent overselling."""
        result = await self.db.execute(
            select(InventoryLedger)
            .where(InventoryLedger.product_id == product_id)
            .with_for_update()
        )
        return result.scalar_one_or_none()

    async def create(
        self,
        *,
        merchant_id: UUID,
        product_id: UUID,
        quantity: int,
    ) -> InventoryLedger:
        row = InventoryLedger(
            merchant_id=merchant_id,
            product_id=product_id,
            quantity=quantity,
            reserved_quantity=0,
        )
        self.db.add(row)
        await self.db.flush()
        await self.db.refresh(row)
        return row

    async def adjust(self, ledger: InventoryLedger, delta: int) -> InventoryLedger:
        new_qty = ledger.quantity + delta
        if new_qty < 0:
            raise ValueError("stock_would_go_negative")
        ledger.quantity = new_qty
        await self.db.flush()
        await self.db.refresh(ledger)
        return ledger
