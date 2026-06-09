from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class BroadcastRequest(BaseModel):
    merchant_id: str
    message: str
    image_url: str | None = None


@router.post("/broadcast")
async def send_broadcast(payload: BroadcastRequest) -> dict:
    """Send a message to all opted-in customers for a given merchant."""
    raise NotImplementedError
