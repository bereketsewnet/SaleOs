from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class KnowledgeFilePublic(BaseModel):
    id: UUID
    filename: str
    file_type: str
    size_bytes: int
    status: str
    error_message: str | None
    chunk_count: int
    uploaded_at: datetime

    model_config = {"from_attributes": True}
