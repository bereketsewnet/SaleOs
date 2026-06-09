from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.knowledge_base import (
    KnowledgeFileStatus,
    MerchantKnowledgeChunk,
    MerchantKnowledgeFile,
)


class KnowledgeBaseRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list_for_merchant(self, merchant_id: UUID) -> list[MerchantKnowledgeFile]:
        result = await self.db.execute(
            select(MerchantKnowledgeFile)
            .where(MerchantKnowledgeFile.merchant_id == merchant_id)
            .order_by(MerchantKnowledgeFile.uploaded_at.desc())
        )
        return list(result.scalars().all())

    async def count_for_merchant(self, merchant_id: UUID) -> int:
        rows = await self.list_for_merchant(merchant_id)
        return len(rows)

    async def get_scoped(
        self, file_id: UUID, merchant_id: UUID
    ) -> MerchantKnowledgeFile | None:
        result = await self.db.execute(
            select(MerchantKnowledgeFile).where(
                MerchantKnowledgeFile.id == file_id,
                MerchantKnowledgeFile.merchant_id == merchant_id,
            )
        )
        return result.scalar_one_or_none()

    async def create_file(
        self,
        *,
        merchant_id: UUID,
        filename: str,
        file_type: str,
        size_bytes: int,
        minio_object_key: str,
    ) -> MerchantKnowledgeFile:
        row = MerchantKnowledgeFile(
            merchant_id=merchant_id,
            filename=filename,
            file_type=file_type,
            size_bytes=size_bytes,
            minio_object_key=minio_object_key,
            status=KnowledgeFileStatus.PROCESSING,
        )
        self.db.add(row)
        await self.db.flush()
        await self.db.refresh(row)
        return row

    async def mark_ready(
        self, file: MerchantKnowledgeFile, *, chunk_count: int
    ) -> None:
        file.status = KnowledgeFileStatus.READY
        file.chunk_count = chunk_count
        file.error_message = None
        await self.db.flush()

    async def mark_failed(
        self, file: MerchantKnowledgeFile, *, error: str
    ) -> None:
        file.status = KnowledgeFileStatus.FAILED
        file.error_message = error[:500]
        await self.db.flush()

    async def add_chunks(
        self,
        *,
        file: MerchantKnowledgeFile,
        chunks: list[dict],
    ) -> None:
        for c in chunks:
            self.db.add(
                MerchantKnowledgeChunk(
                    file_id=file.id,
                    merchant_id=file.merchant_id,
                    chunk_index=c["chunk_index"],
                    content=c["content"],
                    embedding=c.get("embedding"),
                    token_count=c.get("token_count", 0),
                )
            )
        await self.db.flush()

    async def delete_file(self, file: MerchantKnowledgeFile) -> None:
        await self.db.execute(
            delete(MerchantKnowledgeChunk).where(
                MerchantKnowledgeChunk.file_id == file.id
            )
        )
        await self.db.delete(file)
        await self.db.flush()

    async def list_chunks_for_merchant(
        self, merchant_id: UUID
    ) -> list[MerchantKnowledgeChunk]:
        result = await self.db.execute(
            select(MerchantKnowledgeChunk).where(
                MerchantKnowledgeChunk.merchant_id == merchant_id
            )
        )
        return list(result.scalars().all())
