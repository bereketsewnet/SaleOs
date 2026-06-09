from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.telegram import TelegramBotConfig, TelegramChannelPost


class TelegramChannelRepository:
    """Channel binding (on telegram_bot_configs) and channel_posts ingest/list."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def bind_channel(
        self,
        config: TelegramBotConfig,
        *,
        channel_id: int,
        channel_username: str | None,
        channel_title: str | None,
    ) -> TelegramBotConfig:
        config.channel_id = channel_id
        config.channel_username = channel_username
        config.channel_title = channel_title
        await self.db.flush()
        await self.db.refresh(config)
        return config

    async def unbind_channel(self, config: TelegramBotConfig) -> TelegramBotConfig:
        config.channel_id = None
        config.channel_username = None
        config.channel_title = None
        await self.db.flush()
        await self.db.refresh(config)
        return config

    async def find_existing_post(
        self, channel_id: int, message_id: int
    ) -> TelegramChannelPost | None:
        result = await self.db.execute(
            select(TelegramChannelPost).where(
                TelegramChannelPost.channel_id == channel_id,
                TelegramChannelPost.message_id == message_id,
            )
        )
        return result.scalar_one_or_none()

    async def create_post(
        self,
        *,
        merchant_id: UUID,
        channel_id: int,
        message_id: int,
        caption: str | None,
        photo_file_id: str | None,
        posted_by_admin: bool = False,
        product_id: UUID | None = None,
    ) -> TelegramChannelPost:
        post = TelegramChannelPost(
            merchant_id=merchant_id,
            channel_id=channel_id,
            message_id=message_id,
            caption=caption,
            photo_file_id=photo_file_id,
            posted_by_admin=posted_by_admin,
            product_id=product_id,
        )
        self.db.add(post)
        await self.db.flush()
        await self.db.refresh(post)
        return post

    async def upsert_post(
        self,
        *,
        merchant_id: UUID,
        channel_id: int,
        message_id: int,
        caption: str | None,
        photo_file_id: str | None,
        posted_by_admin: bool,
        product_id: UUID | None,
    ) -> TelegramChannelPost:
        """Race-safe ingest: existing row keeps its True flags and product_id;
        these are only promoted when the caller provides truthier values."""
        existing = await self.find_existing_post(channel_id, message_id)
        if existing is not None:
            if posted_by_admin and not existing.posted_by_admin:
                existing.posted_by_admin = True
            if product_id and not existing.product_id:
                existing.product_id = product_id
            if caption and not existing.caption:
                existing.caption = caption
            if photo_file_id and not existing.photo_file_id:
                existing.photo_file_id = photo_file_id
            await self.db.flush()
            await self.db.refresh(existing)
            return existing
        return await self.create_post(
            merchant_id=merchant_id,
            channel_id=channel_id,
            message_id=message_id,
            caption=caption,
            photo_file_id=photo_file_id,
            posted_by_admin=posted_by_admin,
            product_id=product_id,
        )

    async def list_by_product(
        self, product_id: UUID
    ) -> list[TelegramChannelPost]:
        result = await self.db.execute(
            select(TelegramChannelPost).where(TelegramChannelPost.product_id == product_id)
        )
        return list(result.scalars().all())

    async def delete_posts(self, posts: list[TelegramChannelPost]) -> None:
        for p in posts:
            await self.db.delete(p)
        await self.db.flush()

    async def list_for_merchant(
        self, merchant_id: UUID, limit: int = 50, offset: int = 0
    ) -> list[TelegramChannelPost]:
        result = await self.db.execute(
            select(TelegramChannelPost)
            .where(TelegramChannelPost.merchant_id == merchant_id)
            .order_by(TelegramChannelPost.posted_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())
