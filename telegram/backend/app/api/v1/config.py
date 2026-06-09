from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, status

from app.core.config import settings
from app.services.bot_manager import get_bot_manager

router = APIRouter()


def _require_service_token(x_service_token: str = Header(...)) -> None:
    if x_service_token != settings.X_SERVICE_TOKEN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid service token")


@router.post("/internal/reload-bot/{merchant_id}", status_code=status.HTTP_202_ACCEPTED)
async def reload_bot(merchant_id: UUID, _: None = Depends(_require_service_token)) -> dict:
    """Called by Core after a merchant saves/deletes their bot config in the admin panel."""
    started = await get_bot_manager().reload(merchant_id)
    return {"merchant_id": str(merchant_id), "started": started}
