from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text, Uuid, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class KnowledgeFileStatus:
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"


class MerchantKnowledgeFile(Base):
    __tablename__ = "merchant_knowledge_files"
    __table_args__ = (Index("ix_kb_files_merchant_id", "merchant_id"),)

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    merchant_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("merchants.id", ondelete="CASCADE"),
        nullable=False,
    )
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_type: Mapped[str] = mapped_column(String(20), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    minio_object_key: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=KnowledgeFileStatus.PROCESSING
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    chunk_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    chunks: Mapped[list["MerchantKnowledgeChunk"]] = relationship(
        "MerchantKnowledgeChunk",
        back_populates="file",
        cascade="all, delete-orphan",
    )


class MerchantKnowledgeChunk(Base):
    __tablename__ = "merchant_knowledge_chunks"
    __table_args__ = (
        Index("ix_kb_chunks_merchant_id", "merchant_id"),
        Index("ix_kb_chunks_file_id", "file_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    file_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("merchant_knowledge_files.id", ondelete="CASCADE"),
        nullable=False,
    )
    merchant_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("merchants.id", ondelete="CASCADE"),
        nullable=False,
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    # Float array stored as JSONB. Plain Python cosine at query time — fine for
    # <1000 chunks per merchant; can swap to pgvector later without schema churn.
    embedding: Mapped[list[float] | None] = mapped_column(JSONB, nullable=True)
    token_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    file: Mapped[MerchantKnowledgeFile] = relationship(
        "MerchantKnowledgeFile", back_populates="chunks"
    )
