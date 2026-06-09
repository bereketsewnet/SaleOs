import io
import mimetypes
import uuid
from pathlib import Path
from uuid import UUID

from minio import Minio
from minio.error import S3Error

from app.core.config import settings

_client: Minio | None = None


def _client_get() -> Minio:
    global _client
    if _client is None:
        _client = Minio(
            endpoint=settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_USE_SSL,
        )
    return _client


def _public_base() -> str:
    """How browsers will reach the bucket. For local dev, swap the Docker hostname
    for localhost so the admin panel's <img src> works."""
    endpoint = settings.MINIO_ENDPOINT
    # In Docker, MINIO_ENDPOINT is "minio:9000". Browsers hit "localhost:9000".
    public_host = endpoint.replace("minio:", "localhost:")
    scheme = "https" if settings.MINIO_USE_SSL else "http"
    return f"{scheme}://{public_host}"


class MediaService:
    """Saves product images to MinIO. Bucket merchant-media is public-read."""

    def __init__(self) -> None:
        self.bucket = settings.MINIO_BUCKET_MEDIA

    def upload_product_image(
        self,
        *,
        merchant_id: UUID,
        data: bytes,
        filename: str,
    ) -> dict:
        ext = Path(filename).suffix.lower() or ".jpg"
        if ext not in {".jpg", ".jpeg", ".png", ".webp", ".gif"}:
            raise ValueError("unsupported_image_type")

        object_key = f"merchants/{merchant_id}/products/{uuid.uuid4().hex}{ext}"
        content_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"

        try:
            _client_get().put_object(
                bucket_name=self.bucket,
                object_name=object_key,
                data=io.BytesIO(data),
                length=len(data),
                content_type=content_type,
            )
        except S3Error as exc:
            raise RuntimeError(f"minio_upload_failed: {exc}") from exc

        url = f"{_public_base()}/{self.bucket}/{object_key}"
        return {"url": url, "bucket": self.bucket, "object_key": object_key}

    def fetch_bytes(self, object_key: str) -> bytes:
        """Used by the publish flow when Telegram svc needs the raw bytes."""
        response = _client_get().get_object(self.bucket, object_key)
        try:
            return response.read()
        finally:
            response.close()
            response.release_conn()

    @staticmethod
    def extract_object_key(url: str) -> str | None:
        """Reverse of upload_product_image — used by publishers that get a URL."""
        marker = f"/{settings.MINIO_BUCKET_MEDIA}/"
        idx = url.find(marker)
        if idx == -1:
            return None
        return url[idx + len(marker) :]
