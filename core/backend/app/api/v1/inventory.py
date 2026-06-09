from fastapi import APIRouter

router = APIRouter()


@router.post("/reserve")
async def reserve_stock() -> dict:
    """Atomic stock reservation — called by microservices via X-Service-Token."""
    raise NotImplementedError


@router.post("/release")
async def release_stock() -> dict:
    """Release reserved stock (e.g. order cancelled)."""
    raise NotImplementedError


@router.get("/{product_id}")
async def get_inventory(product_id: str) -> dict:
    raise NotImplementedError
