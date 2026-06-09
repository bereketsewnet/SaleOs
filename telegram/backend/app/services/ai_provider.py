"""Tiny adapter over Gemini / OpenAI / Claude — single text-in / text-out call.

Used by the #product hashtag parser. The merchant picks the provider; we
read their decrypted key from Core's internal config endpoint.
"""
import json
from typing import Any

import structlog

logger = structlog.get_logger()


class AIError(Exception):
    pass


_DEFAULT_MODELS: dict[str, str] = {
    "GEMINI": "gemini-2.0-flash",
    "OPENAI": "gpt-4.1-mini",
    "CLAUDE": "claude-haiku-4-5-20251001",
}


async def complete_json(
    *,
    provider: str,
    api_key: str,
    model: str | None,
    system_prompt: str,
    user_prompt: str,
) -> dict[str, Any]:
    """Asks the provider to return strict JSON. Returns the parsed dict."""
    if not provider or not api_key:
        raise AIError("ai_not_configured")
    model = model or _DEFAULT_MODELS.get(provider)
    if not model:
        raise AIError("ai_invalid_provider")

    try:
        if provider == "GEMINI":
            text = await _gemini(api_key, model, system_prompt, user_prompt)
        elif provider == "OPENAI":
            text = await _openai(api_key, model, system_prompt, user_prompt)
        elif provider == "CLAUDE":
            text = await _claude(api_key, model, system_prompt, user_prompt)
        else:
            raise AIError("ai_invalid_provider")
    except AIError:
        raise
    except Exception as exc:
        # Quota exhaustion, auth failure, network blip, model 404, etc.
        # Always normalize to AIError so callers can fall back gracefully.
        low = str(exc).lower()
        if "quota" in low or "rate limit" in low or "429" in low:
            kind = "ai_quota_exceeded"
        elif "api key" in low or "unauthorized" in low or "auth" in low or "403" in low:
            kind = "ai_invalid_key"
        elif "model" in low and ("not found" in low or "404" in low):
            kind = "ai_invalid_model"
        else:
            kind = "ai_call_failed"
        logger.warning(
            "ai_call_failed",
            provider=provider,
            model=model,
            kind=kind,
            error_type=type(exc).__name__,
            error=str(exc)[:300],
        )
        raise AIError(kind) from exc

    return _parse_json(text)


async def complete_text(
    *,
    provider: str,
    api_key: str,
    model: str | None,
    system_prompt: str,
    user_prompt: str,
    max_tokens: int = 800,
) -> str:
    """Free-form text completion. Used by the reply agent."""
    if not provider or not api_key:
        raise AIError("ai_not_configured")
    model = model or _DEFAULT_MODELS.get(provider)
    if not model:
        raise AIError("ai_invalid_provider")
    try:
        if provider == "GEMINI":
            return await _gemini_text(api_key, model, system_prompt, user_prompt, max_tokens)
        if provider == "OPENAI":
            return await _openai_text(api_key, model, system_prompt, user_prompt, max_tokens)
        if provider == "CLAUDE":
            return await _claude_text(api_key, model, system_prompt, user_prompt, max_tokens)
        raise AIError("ai_invalid_provider")
    except AIError:
        raise
    except Exception as exc:
        raise _normalize_error(provider, model, exc) from exc


async def vision_describe(
    *,
    provider: str,
    api_key: str,
    model: str | None,
    image_urls: list[str],
    language_hint: str | None = None,
) -> str:
    """Run vision over up to 4 product images. Returns a concise identifier text."""
    if not provider or not api_key:
        raise AIError("ai_not_configured")
    if not image_urls:
        raise AIError("ai_no_images")
    model = model or _DEFAULT_MODELS.get(provider)
    if not model:
        raise AIError("ai_invalid_provider")
    urls = [_internal_url(u) for u in image_urls[:4]]
    lang_line = (
        f"Reply in the language hint provided: {language_hint}. "
        if language_hint and language_hint != "AUTO"
        else "Match the implied language of the merchant (Amharic or English). "
    )
    system = (
        "You describe product images for a small business's catalog. "
        "Return ONLY 2–4 short sentences, factual: what the product is, color, "
        "obvious variant/size, and any visible text. No marketing fluff, no price. "
        + lang_line
    )
    try:
        if provider == "GEMINI":
            return await _gemini_vision(api_key, model, system, urls)
        if provider == "OPENAI":
            return await _openai_vision(api_key, model, system, urls)
        if provider == "CLAUDE":
            return await _claude_vision(api_key, model, system, urls)
        raise AIError("ai_invalid_provider")
    except AIError:
        raise
    except Exception as exc:
        raise _normalize_error(provider, model, exc) from exc


def _internal_url(url: str) -> str:
    """Browser-facing URLs point at localhost; swap to Docker internal host."""
    return url.replace("localhost:9000", "minio:9000")


def _normalize_error(provider: str, model: str | None, exc: Exception) -> AIError:
    low = str(exc).lower()
    if "quota" in low or "rate limit" in low or "429" in low:
        kind = "ai_quota_exceeded"
    elif "api key" in low or "unauthorized" in low or "auth" in low or "403" in low:
        kind = "ai_invalid_key"
    elif "model" in low and ("not found" in low or "404" in low):
        kind = "ai_invalid_model"
    else:
        kind = "ai_call_failed"
    logger.warning(
        "ai_call_failed",
        provider=provider,
        model=model,
        kind=kind,
        error_type=type(exc).__name__,
        error=str(exc)[:300],
    )
    return AIError(kind)


async def _gemini_text(api_key, model, system_prompt, user_prompt, max_tokens) -> str:
    import asyncio

    import google.generativeai as genai

    genai.configure(api_key=api_key)
    gm = genai.GenerativeModel(model_name=model, system_instruction=system_prompt)
    loop = asyncio.get_running_loop()
    resp = await loop.run_in_executor(
        None,
        lambda: gm.generate_content(
            user_prompt,
            generation_config={"max_output_tokens": max_tokens},
        ),
    )
    return resp.text or ""


async def _openai_text(api_key, model, system_prompt, user_prompt, max_tokens) -> str:
    from openai import AsyncOpenAI

    client = AsyncOpenAI(api_key=api_key)
    resp = await client.chat.completions.create(
        model=model,
        max_tokens=max_tokens,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )
    return resp.choices[0].message.content or ""


async def _claude_text(api_key, model, system_prompt, user_prompt, max_tokens) -> str:
    from anthropic import AsyncAnthropic

    client = AsyncAnthropic(api_key=api_key)
    resp = await client.messages.create(
        model=model,
        max_tokens=max_tokens,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
    )
    return "".join(getattr(p, "text", "") for p in (resp.content or []))


async def _gemini_vision(api_key, model, system_prompt, urls) -> str:
    import asyncio
    import io

    import google.generativeai as genai
    import httpx
    from PIL import Image

    async def fetch_image(url: str) -> Image.Image:
        async with httpx.AsyncClient(timeout=15.0) as client:
            r = await client.get(url)
            r.raise_for_status()
            return Image.open(io.BytesIO(r.content))

    images = []
    for u in urls:
        try:
            images.append(await fetch_image(u))
        except Exception as exc:
            logger.warning("vision_fetch_failed", url=u, error=str(exc))
    if not images:
        raise AIError("ai_no_images")

    genai.configure(api_key=api_key)
    gm = genai.GenerativeModel(model_name=model, system_instruction=system_prompt)
    loop = asyncio.get_running_loop()
    resp = await loop.run_in_executor(
        None,
        lambda: gm.generate_content(["Describe this product:", *images]),
    )
    return (resp.text or "").strip()


async def _openai_vision(api_key, model, system_prompt, urls) -> str:
    from openai import AsyncOpenAI

    # OpenAI accepts public URLs; we pass the localhost-rewritten internal URL,
    # but OpenAI fetches it from their server — so we must base64-encode instead.
    import base64

    import httpx

    parts: list[dict] = [{"type": "text", "text": "Describe this product."}]
    async with httpx.AsyncClient(timeout=15.0) as client:
        for u in urls:
            try:
                r = await client.get(u)
                r.raise_for_status()
                b64 = base64.b64encode(r.content).decode()
                mime = r.headers.get("content-type", "image/jpeg")
                parts.append(
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:{mime};base64,{b64}"},
                    }
                )
            except Exception as exc:
                logger.warning("vision_fetch_failed", url=u, error=str(exc))

    if len(parts) <= 1:
        raise AIError("ai_no_images")

    oa = AsyncOpenAI(api_key=api_key)
    resp = await oa.chat.completions.create(
        model=model,
        max_tokens=400,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": parts},
        ],
    )
    return (resp.choices[0].message.content or "").strip()


async def _claude_vision(api_key, model, system_prompt, urls) -> str:
    import base64

    import httpx
    from anthropic import AsyncAnthropic

    content: list[dict] = [{"type": "text", "text": "Describe this product."}]
    async with httpx.AsyncClient(timeout=15.0) as client:
        for u in urls:
            try:
                r = await client.get(u)
                r.raise_for_status()
                b64 = base64.b64encode(r.content).decode()
                mime = r.headers.get("content-type", "image/jpeg")
                content.append(
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": mime,
                            "data": b64,
                        },
                    }
                )
            except Exception as exc:
                logger.warning("vision_fetch_failed", url=u, error=str(exc))

    if len(content) <= 1:
        raise AIError("ai_no_images")

    client = AsyncAnthropic(api_key=api_key)
    resp = await client.messages.create(
        model=model,
        max_tokens=400,
        system=system_prompt,
        messages=[{"role": "user", "content": content}],
    )
    return "".join(getattr(p, "text", "") for p in (resp.content or [])).strip()


async def _gemini(api_key: str, model: str, system_prompt: str, user_prompt: str) -> str:
    import google.generativeai as genai

    genai.configure(api_key=api_key)
    gm = genai.GenerativeModel(
        model_name=model,
        system_instruction=system_prompt,
    )
    # google-generativeai SDK is sync; run in thread.
    import asyncio
    loop = asyncio.get_running_loop()
    resp = await loop.run_in_executor(
        None, lambda: gm.generate_content(user_prompt)
    )
    return resp.text or ""


async def _openai(api_key: str, model: str, system_prompt: str, user_prompt: str) -> str:
    from openai import AsyncOpenAI

    client = AsyncOpenAI(api_key=api_key)
    resp = await client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        response_format={"type": "json_object"},
    )
    return resp.choices[0].message.content or ""


async def _claude(api_key: str, model: str, system_prompt: str, user_prompt: str) -> str:
    from anthropic import AsyncAnthropic

    client = AsyncAnthropic(api_key=api_key)
    resp = await client.messages.create(
        model=model,
        max_tokens=1024,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
    )
    parts = resp.content or []
    return "".join(getattr(p, "text", "") for p in parts)


def _parse_json(text: str) -> dict[str, Any]:
    """Strip code fences if present and parse."""
    t = text.strip()
    if t.startswith("```"):
        # ```json\n...\n```  →  ...
        t = t.split("\n", 1)[1] if "\n" in t else t[3:]
        if t.endswith("```"):
            t = t[: -3]
    t = t.strip()
    try:
        return json.loads(t)
    except json.JSONDecodeError as exc:
        logger.warning("ai_json_parse_failed", raw=text[:200], error=str(exc))
        raise AIError("ai_invalid_json") from exc
