from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.redis import close_redis
from app.api.v1 import broadcasts, channel_admin, chat, config, ocr, publish, webhook
from app.services.bot_manager import get_bot_manager

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("saleos_telegram_starting", env=settings.APP_ENV)
    manager = get_bot_manager()
    await manager.start_all()
    try:
        yield
    finally:
        await manager.stop_all()
        await close_redis()
        logger.info("saleos_telegram_shutdown")


app = FastAPI(
    title="SaleOS Telegram API",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(config.router, prefix="/api/v1/telegram", tags=["config"])
app.include_router(webhook.router, prefix="/api/v1/telegram", tags=["webhook"])
app.include_router(broadcasts.router, prefix="/api/v1/telegram", tags=["broadcasts"])
app.include_router(publish.router, prefix="/api/v1/telegram", tags=["publish"])
app.include_router(channel_admin.router, prefix="/api/v1/telegram", tags=["channel-admin"])
app.include_router(ocr.router, prefix="/api/v1/telegram", tags=["ocr"])
app.include_router(chat.router, prefix="/api/v1/telegram", tags=["chat"])


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "service": "saleos-telegram"}
