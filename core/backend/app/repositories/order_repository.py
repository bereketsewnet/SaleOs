from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.order import Order, OrderItem


class OrderRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create_with_items(
        self,
        *,
        merchant_id: UUID,
        channel_source: str,
        customer_info: dict | None,
        notes: str | None,
        total_amount: Decimal,
        order_status: str,
        payment_account_id: UUID | None,
        items: list[dict],  # each: {product_id, quantity, unit_price}
    ) -> Order:
        order = Order(
            merchant_id=merchant_id,
            channel_source=channel_source,
            customer_info=customer_info,
            notes=notes,
            total_amount=total_amount,
            order_status=order_status,
            payment_account_id=payment_account_id,
        )
        self.db.add(order)
        await self.db.flush()
        for it in items:
            self.db.add(
                OrderItem(
                    order_id=order.id,
                    product_id=it["product_id"],
                    quantity=it["quantity"],
                    unit_price=it["unit_price"],
                )
            )
        await self.db.flush()
        await self.db.refresh(order)
        return order

    async def get_with_items(self, order_id: UUID) -> Order | None:
        result = await self.db.execute(
            select(Order)
            .options(selectinload(Order.items))
            .where(Order.id == order_id)
        )
        return result.scalar_one_or_none()

    async def get_scoped(
        self, order_id: UUID, merchant_id: UUID
    ) -> Order | None:
        result = await self.db.execute(
            select(Order)
            .options(selectinload(Order.items))
            .where(Order.id == order_id, Order.merchant_id == merchant_id)
        )
        return result.scalar_one_or_none()

    async def list_for_merchant(
        self,
        merchant_id: UUID,
        *,
        status_eq: str | None = None,
        channel_eq: str | None = None,
        created_after: datetime | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Order]:
        stmt = (
            select(Order)
            .options(selectinload(Order.items))
            .where(Order.merchant_id == merchant_id)
            .order_by(Order.created_at.desc())
        )
        if status_eq:
            stmt = stmt.where(Order.order_status == status_eq)
        if channel_eq:
            stmt = stmt.where(Order.channel_source == channel_eq)
        if created_after:
            stmt = stmt.where(Order.created_at >= created_after)
        stmt = stmt.limit(limit).offset(offset)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def update_status(self, order: Order, new_status: str) -> Order:
        order.order_status = new_status
        await self.db.flush()
        await self.db.refresh(order)
        return order
