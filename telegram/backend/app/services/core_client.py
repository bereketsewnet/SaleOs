from uuid import UUID

import httpx

from app.core.config import settings


class CoreClient:
    """Async HTTP client for calling Core internal endpoints with X-Service-Token."""

    def __init__(self, timeout: float = 10.0) -> None:
        self._base = settings.CORE_SERVICE_URL.rstrip("/")
        self._headers = {"X-Service-Token": settings.X_SERVICE_TOKEN}
        self._timeout = timeout

    async def get_telegram_config(self, merchant_id: UUID) -> dict | None:
        url = f"{self._base}/api/v1/internal/telegram-config/{merchant_id}"
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.get(url, headers=self._headers)
            if resp.status_code == 404:
                return None
            resp.raise_for_status()
            return resp.json()

    async def list_telegram_configs(self) -> list[dict]:
        url = f"{self._base}/api/v1/internal/telegram-configs"
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.get(url, headers=self._headers)
            resp.raise_for_status()
            return resp.json()

    async def bind_channel(
        self,
        merchant_id: UUID,
        *,
        channel_id: int,
        channel_username: str | None,
        channel_title: str | None,
    ) -> None:
        url = f"{self._base}/api/v1/internal/telegram-channel/{merchant_id}/bind"
        payload = {
            "channel_id": channel_id,
            "channel_username": channel_username,
            "channel_title": channel_title,
        }
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.post(url, headers=self._headers, json=payload)
            resp.raise_for_status()

    async def upload_product_image(
        self, merchant_id: UUID, *, filename: str, data: bytes, content_type: str
    ) -> dict:
        url = f"{self._base}/api/v1/internal/products/upload-image"
        files = {"file": (filename, data, content_type)}
        form = {"merchant_id": str(merchant_id)}
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(url, headers=self._headers, files=files, data=form)
            resp.raise_for_status()
            return resp.json()

    async def create_product_from_channel_post(
        self,
        merchant_id: UUID,
        *,
        channel_id: int,
        primary_message_id: int,
        related_message_ids: list[int],
        title: str,
        description: str | None,
        base_price: str | None,
        image_urls: list[str],
    ) -> dict:
        url = f"{self._base}/api/v1/internal/products/from-channel-post"
        payload = {
            "merchant_id": str(merchant_id),
            "channel_id": channel_id,
            "primary_message_id": primary_message_id,
            "related_message_ids": related_message_ids,
            "title": title,
            "description": description,
            "base_price": base_price,
            "image_urls": image_urls,
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(url, headers=self._headers, json=payload)
            resp.raise_for_status()
            return resp.json()

    async def get_product_agent_context(self, product_id: UUID) -> dict | None:
        """Fetch the effective product context (per-product or default fallback)."""
        url = f"{self._base}/api/v1/internal/products/{product_id}/agent-context"
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.get(url, headers=self._headers)
            if resp.status_code == 404:
                return None
            resp.raise_for_status()
            return resp.json()

    async def get_dm_contacts(self, merchant_id: UUID) -> list[dict]:
        url = f"{self._base}/api/v1/internal/telegram-dm-contacts/{merchant_id}"
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.get(url, headers=self._headers)
            resp.raise_for_status()
            return resp.json()

    async def get_merchant_catalog(self, merchant_id: UUID, limit: int = 30) -> list[dict]:
        url = f"{self._base}/api/v1/internal/merchants/{merchant_id}/catalog"
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.get(url, headers=self._headers, params={"limit": limit})
            resp.raise_for_status()
            return resp.json()

    async def query_knowledge_base(
        self, merchant_id: UUID, *, query: str, top_k: int = 4
    ) -> list[str]:
        url = f"{self._base}/api/v1/internal/knowledge-base/query"
        payload = {
            "merchant_id": str(merchant_id),
            "query": query,
            "top_k": top_k,
        }
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(url, headers=self._headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
            return list(data.get("chunks") or [])

    async def get_product_for_channel_message(
        self, merchant_id: UUID, channel_id: int, message_id: int
    ) -> UUID | None:
        url = f"{self._base}/api/v1/internal/telegram-channel/{merchant_id}/product-by-message"
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.get(
                url,
                headers=self._headers,
                params={"channel_id": channel_id, "message_id": message_id},
            )
            resp.raise_for_status()
            data = resp.json()
            pid = data.get("product_id")
            return UUID(pid) if pid else None

    async def set_ocr_result(self, product_id: UUID, identifier_text: str) -> None:
        url = f"{self._base}/api/v1/internal/products/{product_id}/ocr-result"
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.patch(
                url, headers=self._headers, json={"identifier": identifier_text}
            )
            resp.raise_for_status()

    async def update_order_customer_details(
        self,
        *,
        order_id: UUID,
        name: str | None = None,
        phone: str | None = None,
        address: str | None = None,
    ) -> dict:
        url = f"{self._base}/api/v1/internal/orders/{order_id}/customer-details"
        payload = {"name": name, "phone": phone, "address": address}
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.patch(url, headers=self._headers, json=payload)
            resp.raise_for_status()
            return resp.json()

    async def create_order_from_channel_comment(
        self,
        *,
        merchant_id: UUID,
        product_id: UUID,
        telegram_user_id: int,
        customer_name: str | None,
        receipt_bytes: bytes,
        receipt_filename: str,
        content_type: str = "image/jpeg",
    ) -> dict:
        url = f"{self._base}/api/v1/internal/orders/from-channel-comment"
        files = {"file": (receipt_filename, receipt_bytes, content_type)}
        form = {
            "merchant_id": str(merchant_id),
            "product_id": str(product_id),
            "telegram_user_id": str(telegram_user_id),
        }
        if customer_name:
            form["customer_name"] = customer_name
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(url, headers=self._headers, files=files, data=form)
            resp.raise_for_status()
            return resp.json()

    async def save_channel_post(
        self,
        merchant_id: UUID,
        *,
        channel_id: int,
        message_id: int,
        caption: str | None,
        photo_file_id: str | None,
        posted_by_admin: bool = False,
        product_id: UUID | None = None,
    ) -> None:
        url = f"{self._base}/api/v1/internal/telegram-channel/{merchant_id}/posts"
        payload = {
            "channel_id": channel_id,
            "message_id": message_id,
            "caption": caption,
            "photo_file_id": photo_file_id,
            "posted_by_admin": posted_by_admin,
            "product_id": str(product_id) if product_id else None,
        }
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.post(url, headers=self._headers, json=payload)
            resp.raise_for_status()
