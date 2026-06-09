from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel

from app.core.config import settings
from app.services.publisher import PublisherError, publish_product

router = APIRouter()


def _require_service_token(x_service_token: str = Header(...)) -> None:
    if x_service_token != settings.X_SERVICE_TOKEN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid service token")


class PublishProductRequest(BaseModel):
    merchant_id: UUID
    product_id: UUID
    title: str
    description: str | None = None
    base_price: str | None = None
    image_urls: list[str] = []


@router.post("/internal/publish-product")
async def publish_product_endpoint(
    payload: PublishProductRequest, _: None = Depends(_require_service_token)
) -> dict:
    try:
        result = await publish_product(
            merchant_id=payload.merchant_id,
            product_id=payload.product_id,
            title=payload.title,
            description=payload.description,
            base_price=payload.base_price,
            image_urls=payload.image_urls,
        )
    except PublisherError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return {"published": True, **result}
