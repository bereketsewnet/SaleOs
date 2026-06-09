"""Embedding providers. Each merchant supplies their own AI key — we use the
same provider for embeddings when it has them (OpenAI / Gemini). Claude has no
native embedding API, so claude-using merchants fall back to a keyword score.

Returns a list of float vectors, one per input string. Cosine similarity
elsewhere can compare across providers as long as both sides use the same one
within a single merchant's corpus + query."""
from __future__ import annotations

import math

import structlog

logger = structlog.get_logger()


class EmbeddingError(Exception):
    pass


EMBEDDING_MODELS = {
    "OPENAI": "text-embedding-3-small",
    "GEMINI": "text-embedding-004",
}


def supports_embeddings(provider: str | None) -> bool:
    return (provider or "").upper() in EMBEDDING_MODELS


async def embed_texts(
    *, provider: str, api_key: str, texts: list[str]
) -> list[list[float]]:
    if not texts:
        return []
    provider = (provider or "").upper()
    if provider == "OPENAI":
        return await _embed_openai(api_key, texts)
    if provider == "GEMINI":
        return await _embed_gemini(api_key, texts)
    raise EmbeddingError(f"provider {provider} does not support embeddings")


async def _embed_openai(api_key: str, texts: list[str]) -> list[list[float]]:
    from openai import AsyncOpenAI

    client = AsyncOpenAI(api_key=api_key)
    try:
        resp = await client.embeddings.create(
            model=EMBEDDING_MODELS["OPENAI"],
            input=texts,
        )
    except Exception as exc:
        raise EmbeddingError(f"openai embed failed: {exc}") from exc
    return [d.embedding for d in resp.data]


async def _embed_gemini(api_key: str, texts: list[str]) -> list[list[float]]:
    import google.generativeai as genai

    genai.configure(api_key=api_key)
    out: list[list[float]] = []
    for text in texts:
        try:
            res = genai.embed_content(
                model="models/" + EMBEDDING_MODELS["GEMINI"],
                content=text,
            )
        except Exception as exc:
            raise EmbeddingError(f"gemini embed failed: {exc}") from exc
        out.append(list(res["embedding"]))
    return out


def cosine_similarity(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = 0.0
    norm_a = 0.0
    norm_b = 0.0
    for x, y in zip(a, b):
        dot += x * y
        norm_a += x * x
        norm_b += y * y
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot / (math.sqrt(norm_a) * math.sqrt(norm_b))
