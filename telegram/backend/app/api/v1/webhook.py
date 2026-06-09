from fastapi import APIRouter, Request, Response

router = APIRouter()


@router.post("/webhook/{merchant_id}")
async def receive_update(merchant_id: str, request: Request) -> Response:
    """
    Telegram delivers bot updates here via webhook.
    Dispatches to aiogram for handler processing.
    Returns 200 immediately — Telegram retries on non-200.
    """
    raise NotImplementedError
