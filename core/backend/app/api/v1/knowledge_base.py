"""Admin routes for managing the merchant's knowledge base."""
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.middleware.auth import get_current_user, require_admin
from app.models.user import User
from app.schemas.knowledge_base import KnowledgeFilePublic
from app.services.knowledge_base_service import (
    KBFileNotFound,
    KBFileTooLarge,
    KBFileTypeUnsupported,
    KBLimitExceeded,
    KnowledgeBaseService,
    MAX_FILES_PER_MERCHANT,
)

router = APIRouter()


def _require_merchant(user: User) -> UUID:
    if not user.merchant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="no_merchant_context"
        )
    return user.merchant_id


@router.get("/", response_model=list[KnowledgeFilePublic])
async def list_files(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[KnowledgeFilePublic]:
    merchant_id = _require_merchant(user)
    files = await KnowledgeBaseService(db).list_files(merchant_id)
    return [KnowledgeFilePublic.model_validate(f) for f in files]


@router.post("/", response_model=KnowledgeFilePublic, status_code=status.HTTP_201_CREATED)
async def upload_file(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_admin),
) -> KnowledgeFilePublic:
    merchant_id = _require_merchant(user)
    if not file.filename:
        raise HTTPException(status_code=400, detail="missing_filename")
    data = await file.read()
    try:
        row = await KnowledgeBaseService(db).upload_file(
            merchant_id=merchant_id, filename=file.filename, data=data
        )
    except KBLimitExceeded:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": "kb_limit_exceeded",
                "max_files": MAX_FILES_PER_MERCHANT,
            },
        )
    except KBFileTooLarge:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="kb_file_too_large",
        )
    except KBFileTypeUnsupported as exc:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=str(exc),
        )
    return KnowledgeFilePublic.model_validate(row)


@router.delete("/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_file(
    file_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_admin),
) -> None:
    merchant_id = _require_merchant(user)
    try:
        await KnowledgeBaseService(db).delete_file(
            file_id=file_id, merchant_id=merchant_id
        )
    except KBFileNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not_found")
