from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class TelegramBotConfig(Base):
    __tablename__ = "telegram_bot_configs"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    merchant_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("merchants.id"), unique=True, nullable=False
    )
    # Stored encrypted — never expose raw token in API responses
    bot_token: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    bot_username: Mapped[str | None] = mapped_column(String(100), nullable=True)
    # Telegram channel_id — auto-detected when bot is promoted as admin in the channel
    channel_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True, unique=True)
    channel_username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    channel_title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # Telegram group_id of the linked Discussion Group — set after merchant verifies
    discussion_group_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    welcome_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    # AMHARIC | ENGLISH | AUTO
    language_preference: Mapped[str] = mapped_column(String(20), default="AUTO")
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)

    # Telegram-specific brand voice. Each platform (TikTok, IG, FB) has its own.
    business_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    business_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    system_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Defaults inherited by every product whose own identifier/instructions are blank.
    default_product_identifier: Mapped[str | None] = mapped_column(Text, nullable=True)
    default_product_instructions: Mapped[str | None] = mapped_column(Text, nullable=True)

    # AI agent — provider + encrypted API key + model. Used by reply/autopost/parse agents.
    # ai_provider: GEMINI | OPENAI | CLAUDE
    ai_provider: Mapped[str | None] = mapped_column(String(20), nullable=True)
    ai_api_key: Mapped[str | None] = mapped_column(Text, nullable=True)  # Fernet-encrypted
    ai_model: Mapped[str | None] = mapped_column(String(100), nullable=True)
    # Behavior toggles
    ai_auto_reply_dm: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="false", default=False
    )
    ai_auto_reply_comments: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="false", default=False
    )
    ai_parse_hashtag_products: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="true", default=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )


class TelegramCustomer(Base):
    """Maps a Telegram user to a SaleOS merchant. Optional link to a registered SaleOS user."""
    __tablename__ = "telegram_customers"
    __table_args__ = (
        UniqueConstraint("merchant_id", "telegram_user_id", name="uq_merchant_telegram_user"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    merchant_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("merchants.id"), nullable=False
    )
    telegram_user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    chat_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    first_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # Filled when customer optionally shares phone via bot
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    # Filled when customer completes optional SaleOS login (for purchase history)
    saleos_user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id"), nullable=True
    )


class TelegramChannelPost(Base):
    """
    Every post we see in the merchant's Telegram channel.
    - Posts coming from the admin panel ("Publish to channel"): posted_by_admin=True, product_id set.
    - Posts merchant made manually inside Telegram: posted_by_admin=False, product_id None.
    The bot's channel_post handler captures both kinds.
    """
    __tablename__ = "telegram_channel_posts"
    __table_args__ = (
        UniqueConstraint("channel_id", "message_id", name="uq_channel_message"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    merchant_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("merchants.id"), nullable=False, index=True
    )
    channel_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    message_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    caption: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Telegram's file_id for the largest photo size (resolvable to a URL via Bot API).
    photo_file_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    posted_by_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    # Filled when post was created via the admin panel from a specific product.
    product_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("products.id", ondelete="SET NULL"), nullable=True
    )
    posted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class TelegramChatSession(Base):
    """Tracks active bot conversations. FSM state lives in Redis; this row tracks timestamps."""
    __tablename__ = "telegram_chat_sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    customer_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("telegram_customers.id"), nullable=False
    )
    merchant_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("merchants.id"), nullable=False
    )
    # Redis key pattern: telegram:fsm:{merchant_id}:{chat_id}
    redis_fsm_key: Mapped[str] = mapped_column(String(200), nullable=False)
    last_interaction: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class TelegramDMContact(Base):
    """Contact info the AI agent can share with customers per instructions.
    Telegram-specific — each microservice has its own set, matching brand voice / AI fields."""
    __tablename__ = "telegram_dm_contacts"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    merchant_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("merchants.id"), nullable=False, index=True
    )
    # TELEGRAM_USERNAME | PHONE | EMAIL | ADDRESS | OTHER
    kind: Mapped[str] = mapped_column(String(32), nullable=False)
    value: Mapped[str] = mapped_column(String(255), nullable=False)
    label: Mapped[str | None] = mapped_column(String(80), nullable=True)
    position: Mapped[int] = mapped_column(
        # Smaller position = higher priority; "first phone" = position 0 active.
        Integer, nullable=False, server_default="0", default=0
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="true", default=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
