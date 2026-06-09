"""Internal OCR endpoint. Core calls here when a merchant asks to identify a
product by its images. We run vision with the merchant's configured AI provider,
then PATCH the result back to Core."""
import asyncio
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel

from app.core.config import settings
from app.services.ai_provider import AIError, vision_describe
from app.services.bot_manager import get_bot_manager
from app.services.core_client import CoreClient

logger = structlog.get_logger()
router = APIRouter()


def _require_service_token(x_service_token: str = Header(...)) -> None:
    if x_service_token != settings.X_SERVICE_TOKEN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid service token")


class OCRProductRequest(BaseModel):
    merchant_id: UUID
    product_id: UUID
    image_urls: list[str]


@router.post("/internal/ocr-product", status_code=status.HTTP_202_ACCEPTED)
async def ocr_product(
    payload: OCRProductRequest, _: None = Depends(_require_service_token)
) -> dict:
    """Schedules vision in the background and returns immediately."""
    asyncio.create_task(_run(payload))
    return {"queued": True}


async def _run(payload: OCRProductRequest) -> None:
    bundle = get_bot_manager().get_bot_for_merchant(payload.merchant_id)
    if bundle is None:
        logger.warning("ocr_no_bot_context", merchant_id=str(payload.merchant_id))
        # Fall back to fetching fresh cfg from Core
        cfg = await CoreClient().get_telegram_config(payload.merchant_id)
        if not cfg:
            return
        provider = cfg.get("ai_provider")
        api_key = cfg.get("ai_api_key")
        model = cfg.get("ai_model")
        lang = cfg.get("language_preference")
    else:
        merchant = bundle.dispatcher["merchant"]
        provider = merchant.ai_provider
        api_key = merchant.ai_api_key
        model = merchant.ai_model
        lang = merchant.language_preference

    if not provider or not api_key:
        logger.info(
            "ocr_skipped_no_ai",
            merchant_id=str(payload.merchant_id),
            product_id=str(payload.product_id),
        )
        return

    try:
        identifier_text = await vision_describe(
            provider=provider,
            api_key=api_key,
            model=model,
            image_urls=payload.image_urls,
            language_hint=lang,
        )
    except AIError as exc:
        logger.warning(
            "vision_describe_failed",
            merchant_id=str(payload.merchant_id),
            product_id=str(payload.product_id),
            error=str(exc),
        )
        return

    if not identifier_text.strip():
        return

    try:
        await CoreClient().set_ocr_result(payload.product_id, identifier_text.strip())
        logger.info(
            "vision_describe_ok",
            merchant_id=str(payload.merchant_id),
            product_id=str(payload.product_id),
            chars=len(identifier_text),
        )
    except Exception as exc:
        logger.warning(
            "vision_save_failed",
            merchant_id=str(payload.merchant_id),
            product_id=str(payload.product_id),
            error=str(exc),
        )
