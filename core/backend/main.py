from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.v1 import (
    auth,
    merchants,
    merchant_profile,
    products,
    inventory,
    orders,
    internal,
    payment_accounts,
    public_catalog,
    telegram_channel,
    telegram_config,
    telegram_dm_contacts,
    ws as ws_routes,
)

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("saleos_core_starting", env=settings.APP_ENV)
    yield
    logger.info("saleos_core_shutdown")


app = FastAPI(
    title="SaleOS Core API",
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

app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(merchants.router, prefix="/api/v1/core/merchants", tags=["merchants"])
app.include_router(
    merchant_profile.router,
    prefix="/api/v1/core/merchant-profile",
    tags=["merchant-profile"],
)
app.include_router(products.router, prefix="/api/v1/core/products", tags=["products"])
app.include_router(inventory.router, prefix="/api/v1/core/inventory", tags=["inventory"])
app.include_router(orders.router, prefix="/api/v1/core/orders", tags=["orders"])
app.include_router(
    payment_accounts.router,
    prefix="/api/v1/core/payment-accounts",
    tags=["payment-accounts"],
)
app.include_router(
    telegram_config.router,
    prefix="/api/v1/core/telegram-config",
    tags=["telegram-config"],
)
app.include_router(
    telegram_channel.router,
    prefix="/api/v1/core/telegram-channel",
    tags=["telegram-channel"],
)
app.include_router(
    telegram_dm_contacts.router,
    prefix="/api/v1/core/telegram-dm-contacts",
    tags=["telegram-dm-contacts"],
)
app.include_router(internal.router, prefix="/api/v1/internal", tags=["internal"])
app.include_router(public_catalog.router, prefix="/api/v1/catalog", tags=["catalog"])

# WebSocket for admin-panel real-time alerts (NEW_ORDER toasts, etc.)
app.add_api_websocket_route("/ws/alerts", ws_routes.alerts_socket)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "service": "saleos-core"}
