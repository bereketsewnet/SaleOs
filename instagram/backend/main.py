from fastapi import FastAPI, Request, Response

app = FastAPI(
    title="SaleOS Instagram API",
    version="1.0.0",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "service": "saleos-instagram"}


@app.post("/api/v1/instagram/webhook/{merchant_id}")
async def receive_webhook(merchant_id: str, request: Request) -> Response:
    """Instagram webhook receiver — Phase 2."""
    return Response(content='{"status":"placeholder"}', media_type="application/json")
