from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def list_orders() -> dict:
    raise NotImplementedError


@router.post("/")
async def create_order() -> dict:
    """Called by microservices after payment verification."""
    raise NotImplementedError


@router.get("/{order_id}")
async def get_order(order_id: str) -> dict:
    raise NotImplementedError


@router.patch("/{order_id}/status")
async def update_order_status(order_id: str) -> dict:
    raise NotImplementedError
