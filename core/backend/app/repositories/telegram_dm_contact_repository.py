from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.telegram import TelegramDMContact


class TelegramDMContactRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list_all(self, merchant_id: UUID) -> list[TelegramDMContact]:
        result = await self.db.execute(
            select(TelegramDMContact)
            .where(TelegramDMContact.merchant_id == merchant_id)
            .order_by(TelegramDMContact.kind.asc(), TelegramDMContact.position.asc())
        )
        return list(result.scalars().all())

    async def list_active(self, merchant_id: UUID) -> list[TelegramDMContact]:
        result = await self.db.execute(
            select(TelegramDMContact)
            .where(
                TelegramDMContact.merchant_id == merchant_id,
                TelegramDMContact.is_active.is_(True),
            )
            .order_by(TelegramDMContact.kind.asc(), TelegramDMContact.position.asc())
        )
        return list(result.scalars().all())

    async def get(self, contact_id: UUID, merchant_id: UUID) -> TelegramDMContact | None:
        result = await self.db.execute(
            select(TelegramDMContact).where(
                TelegramDMContact.id == contact_id,
                TelegramDMContact.merchant_id == merchant_id,
            )
        )
        return result.scalar_one_or_none()

    async def create(
        self,
        *,
        merchant_id: UUID,
        kind: str,
        value: str,
        label: str | None,
        position: int,
        is_active: bool,
    ) -> TelegramDMContact:
        contact = TelegramDMContact(
            merchant_id=merchant_id,
            kind=kind,
            value=value,
            label=label,
            position=position,
            is_active=is_active,
        )
        self.db.add(contact)
        await self.db.flush()
        await self.db.refresh(contact)
        return contact

    async def update(self, contact: TelegramDMContact, **fields) -> TelegramDMContact:
        for k, v in fields.items():
            if v is not None:
                setattr(contact, k, v)
        await self.db.flush()
        await self.db.refresh(contact)
        return contact

    async def delete(self, contact: TelegramDMContact) -> None:
        await self.db.delete(contact)
        await self.db.flush()

    async def reorder(self, merchant_id: UUID, positions: dict[UUID, int]) -> None:
        """Bulk update positions for all listed contacts (scoped to this merchant)."""
        if not positions:
            return
        result = await self.db.execute(
            select(TelegramDMContact).where(
                TelegramDMContact.merchant_id == merchant_id,
                TelegramDMContact.id.in_(list(positions.keys())),
            )
        )
        for contact in result.scalars().all():
            contact.position = positions[contact.id]
        await self.db.flush()
