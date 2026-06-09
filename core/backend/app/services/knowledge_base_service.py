"""Knowledge-base service: handles upload + parse + chunk + embed + similarity
retrieval. Each merchant gets a max of MAX_FILES files; each file produces a
set of chunks stored in `merchant_knowledge_chunks` with optional embedding.
"""
from __future__ import annotations

from uuid import UUID

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.knowledge_base import (
    KnowledgeFileStatus,
    MerchantKnowledgeFile,
)
from app.repositories.knowledge_base_repository import KnowledgeBaseRepository
from app.repositories.telegram_repository import TelegramBotConfigRepository
from app.services.embedding_service import (
    EmbeddingError,
    cosine_similarity,
    embed_texts,
    supports_embeddings,
)
from app.services.knowledge_parsers import (
    ParseError,
    UnsupportedFileType,
    chunk_text,
    detect_file_type,
    extract_text,
)
from app.services.media_service import KnowledgeFileStorage
from app.utils.crypto import decrypt_secret

logger = structlog.get_logger()


MAX_FILES_PER_MERCHANT = 3
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB


class KBLimitExceeded(Exception):
    pass


class KBFileTooLarge(Exception):
    pass


class KBFileTypeUnsupported(Exception):
    pass


class KBFileNotFound(Exception):
    pass


class KnowledgeBaseService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = KnowledgeBaseRepository(db)
        self.storage = KnowledgeFileStorage()
        self.tg_repo = TelegramBotConfigRepository(db)

    async def list_files(self, merchant_id: UUID) -> list[MerchantKnowledgeFile]:
        return await self.repo.list_for_merchant(merchant_id)

    async def upload_file(
        self,
        *,
        merchant_id: UUID,
        filename: str,
        data: bytes,
    ) -> MerchantKnowledgeFile:
        if len(data) == 0:
            raise KBFileTypeUnsupported("empty_file")
        if len(data) > MAX_FILE_SIZE_BYTES:
            raise KBFileTooLarge()
        try:
            file_type = detect_file_type(filename)
        except UnsupportedFileType as exc:
            raise KBFileTypeUnsupported(str(exc)) from exc

        existing = await self.repo.list_for_merchant(merchant_id)
        if len(existing) >= MAX_FILES_PER_MERCHANT:
            raise KBLimitExceeded()

        object_key = self.storage.upload(
            merchant_id=merchant_id, data=data, filename=filename
        )
        row = await self.repo.create_file(
            merchant_id=merchant_id,
            filename=filename,
            file_type=file_type,
            size_bytes=len(data),
            minio_object_key=object_key,
        )
        await self._process(row, data)
        return row

    async def _process(self, file: MerchantKnowledgeFile, data: bytes) -> None:
        try:
            text = extract_text(data, file.filename)
            chunks = chunk_text(text)
            if not chunks:
                await self.repo.mark_failed(file, error="No extractable text in file")
                return

            embeddings = await self._maybe_embed(file.merchant_id, chunks)

            chunk_payload: list[dict] = []
            for idx, chunk in enumerate(chunks):
                emb = embeddings[idx] if embeddings else None
                chunk_payload.append(
                    {
                        "chunk_index": idx,
                        "content": chunk,
                        "embedding": emb,
                        "token_count": len(chunk) // 4,  # rough estimate
                    }
                )
            await self.repo.add_chunks(file=file, chunks=chunk_payload)
            await self.repo.mark_ready(file, chunk_count=len(chunk_payload))
        except (ParseError, UnsupportedFileType) as exc:
            await self.repo.mark_failed(file, error=str(exc))
        except Exception as exc:
            logger.warning(
                "kb_process_unexpected_error",
                file_id=str(file.id),
                error=str(exc),
            )
            await self.repo.mark_failed(file, error=f"Unexpected error: {exc}")

    async def _maybe_embed(
        self, merchant_id: UUID, chunks: list[str]
    ) -> list[list[float]] | None:
        """Embed chunks if the merchant's Telegram AI provider supports it.
        Returns None on any failure — we still store text-only chunks so
        keyword search (BM25-ish) keeps working."""
        cfg = await self.tg_repo.get_by_merchant(merchant_id)
        if not cfg or not cfg.ai_provider or not cfg.ai_api_key:
            return None
        if not supports_embeddings(cfg.ai_provider):
            return None
        try:
            decrypted = decrypt_secret(cfg.ai_api_key)
        except Exception as exc:
            logger.warning(
                "kb_decrypt_key_failed", merchant_id=str(merchant_id), error=str(exc)
            )
            return None
        try:
            return await embed_texts(
                provider=cfg.ai_provider, api_key=decrypted, texts=chunks
            )
        except EmbeddingError as exc:
            logger.warning(
                "kb_embed_failed", merchant_id=str(merchant_id), error=str(exc)
            )
            return None

    async def delete_file(self, *, file_id: UUID, merchant_id: UUID) -> None:
        file = await self.repo.get_scoped(file_id, merchant_id)
        if not file:
            raise KBFileNotFound()
        try:
            self.storage.delete(file.minio_object_key)
        except Exception:
            pass
        await self.repo.delete_file(file)

    async def query(
        self, *, merchant_id: UUID, query: str, top_k: int = 4
    ) -> list[str]:
        """Return the top-k chunk texts most relevant to the query. Uses cosine
        similarity over embeddings when available; falls back to keyword overlap
        when the merchant's provider doesn't have embeddings."""
        all_chunks = await self.repo.list_chunks_for_merchant(merchant_id)
        if not all_chunks:
            return []

        embedded = [c for c in all_chunks if c.embedding]
        if embedded:
            query_emb = await self._embed_query(merchant_id, query)
            if query_emb:
                scored = [
                    (cosine_similarity(query_emb, c.embedding), c) for c in embedded
                ]
                scored.sort(key=lambda x: x[0], reverse=True)
                return [c.content for _, c in scored[:top_k] if _ > 0.05]

        return _keyword_topk(query, [c.content for c in all_chunks], top_k)

    async def _embed_query(
        self, merchant_id: UUID, query: str
    ) -> list[float] | None:
        cfg = await self.tg_repo.get_by_merchant(merchant_id)
        if not cfg or not cfg.ai_provider or not cfg.ai_api_key:
            return None
        if not supports_embeddings(cfg.ai_provider):
            return None
        try:
            decrypted = decrypt_secret(cfg.ai_api_key)
        except Exception:
            return None
        try:
            vecs = await embed_texts(
                provider=cfg.ai_provider, api_key=decrypted, texts=[query]
            )
        except EmbeddingError:
            return None
        return vecs[0] if vecs else None


def _keyword_topk(query: str, texts: list[str], top_k: int) -> list[str]:
    """Simple bag-of-words overlap. Lowercase + split on non-letter chars."""
    import re

    def tokenize(s: str) -> set[str]:
        return {t for t in re.split(r"[^a-zA-Zሀ-፿0-9]+", s.lower()) if t}

    query_tokens = tokenize(query)
    if not query_tokens:
        return texts[:top_k]
    scored: list[tuple[int, str]] = []
    for t in texts:
        overlap = len(query_tokens & tokenize(t))
        if overlap > 0:
            scored.append((overlap, t))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [t for _, t in scored[:top_k]]
