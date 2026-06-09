from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.telegram import TelegramDMContact
from app.repositories.telegram_dm_contact_repository import TelegramDMContactRepository
from app.schemas.telegram_dm_contact import DMContactCreate, DMContactUpdate


class DMContactNotFoundError(Exception):
    pass


class TelegramDMContactService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = TelegramDMContactRepository(db)

    async def list_for_merchant(self, merchant_id: UUID) -> list[TelegramDMContact]:
        return await self.repo.list_all(merchant_id)

    async def create(self, merchant_id: UUID, payload: DMContactCreate) -> TelegramDMContact:
        return await self.repo.create(
            merchant_id=merchant_id,
            kind=payload.kind,
            value=payload.value.strip(),
            label=(payload.label or "").strip() or None,
            position=payload.position,
            is_active=payload.is_active,
        )

    async def update(
        self, contact_id: UUID, merchant_id: UUID, payload: DMContactUpdate
    ) -> TelegramDMContact:
        contact = await self.repo.get(contact_id, merchant_id)
        if not contact:
            raise DMContactNotFoundError()
        return await self.repo.update(
            contact,
            kind=payload.kind,
            value=payload.value.strip() if payload.value is not None else None,
            label=(payload.label or "").strip() or None if payload.label is not None else None,
            position=payload.position,
            is_active=payload.is_active,
        )

    async def delete(self, contact_id: UUID, merchant_id: UUID) -> None:
        contact = await self.repo.get(contact_id, merchant_id)
        if not contact:
            raise DMContactNotFoundError()
        await self.repo.delete(contact)

    async def reorder(self, merchant_id: UUID, positions: dict[UUID, int]) -> None:
        await self.repo.reorder(merchant_id, positions)
