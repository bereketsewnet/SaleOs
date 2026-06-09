"""Verify Telegram Mini App `initData` HMAC and resolve the calling customer.

Spec: https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app

The bot_token is decrypted from `telegram_bot_configs` per merchant. The Mini App
sends the raw initData in the `X-Telegram-Init-Data` header and the merchant_id
either in `X-Merchant-Id` header or the `merchant_id` query param.

In development (`APP_ENV=development`) the client may pass `?dev=1` + `merchant_id=<uuid>`
to skip HMAC verification — useful for opening the Mini App in a plain browser.
"""
from __future__ import annotations

import hashlib
import hmac
import json
from dataclasses import dataclass
from typing import Any
from urllib.parse import parse_qsl
from uuid import UUID

from fastapi import Depends, Header, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.repositories.telegram_repository import TelegramBotConfigRepository
from app.utils.crypto import decrypt_secret


@dataclass(frozen=True)
class TelegramCustomer:
    merchant_id: UUID
    telegram_user_id: int  # 0 if dev mode
    first_name: str | None
    language_code: str | None
    is_dev: bool


def _verify_signature(init_data: str, bot_token: str) -> dict[str, str] | None:
    """Compute HMAC-SHA256("WebAppData", bot_token) over the sorted data_check_string.
    Returns the parsed kv dict on success, None otherwise."""
    if not init_data:
        return None
    pairs = dict(parse_qsl(init_data, strict_parsing=False))
    received_hash = pairs.pop("hash", None)
    if not received_hash:
        return None

    data_check_string = "\n".join(f"{k}={pairs[k]}" for k in sorted(pairs.keys()))
    secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    expected = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, received_hash):
        return None
    return pairs


async def current_telegram_customer(
    x_telegram_init_data: str | None = Header(default=None, alias="X-Telegram-Init-Data"),
    x_merchant_id: str | None = Header(default=None, alias="X-Merchant-Id"),
    merchant_id: UUID | None = Query(default=None),
    dev: int | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> TelegramCustomer:
    mid: UUID | None = merchant_id
    if mid is None and x_merchant_id:
        try:
            mid = UUID(x_merchant_id)
        except ValueError:
            mid = None
    if mid is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="merchant_id_required",
        )

    # Dev bypass — local browser preview without Telegram.
    if settings.APP_ENV == "development" and dev == 1 and not x_telegram_init_data:
        return TelegramCustomer(
            merchant_id=mid,
            telegram_user_id=0,
            first_name="Dev",
            language_code="en",
            is_dev=True,
        )

    if not x_telegram_init_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="initdata_required"
        )

    cfg = await TelegramBotConfigRepository(db).get_by_merchant(mid)
    if not cfg or not cfg.bot_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="bot_not_configured"
        )
    bot_token = decrypt_secret(cfg.bot_token)

    parsed = _verify_signature(x_telegram_init_data, bot_token)
    if parsed is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="initdata_invalid"
        )

    user: dict[str, Any] = {}
    user_raw = parsed.get("user")
    if user_raw:
        try:
            user = json.loads(user_raw)
        except json.JSONDecodeError:
            user = {}
    telegram_user_id = int(user.get("id", 0))
    if telegram_user_id == 0:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="initdata_no_user"
        )

    return TelegramCustomer(
        merchant_id=mid,
        telegram_user_id=telegram_user_id,
        first_name=user.get("first_name"),
        language_code=user.get("language_code"),
        is_dev=False,
    )
