from fastapi import FastAPI, Request, Response

app = FastAPI(
    title="SaleOS TikTok API",
    version="1.0.0",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "service": "saleos-tiktok"}


@app.post("/api/v1/tiktok/webhook/{merchant_id}")
async def receive_webhook(merchant_id: str, request: Request) -> Response:
    """TikTok webhook receiver — Phase 2."""
    return Response(content='{"status":"placeholder"}', media_type="application/json")
