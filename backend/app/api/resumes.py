"""Resume management API routes.

Provides endpoints for:
- POST /resumes/upload — Upload a resume file (PDF, DOCX, TXT)
- POST /resumes/text — Submit resume as pasted text
- GET /resumes — List user's resumes
- POST /resumes/{resume_id}/versions — Save resume to a named version slot
- GET /resumes/versions — List user's resume versions
"""

import io
import logging
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db
from app.models.db import Resume, ResumeVersion
from app.schemas.resume import (
    ResumeListItem,
    ResumeTextInput,
    ResumeUploadResponse,
    ResumeVersionCreate,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/resumes", tags=["resumes"])

# Supported file formats
_ALLOWED_CONTENT_TYPES = {
    "application/pdf": "pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
    "text/plain": "txt",
}
_MAX_FILE_SIZE_MB = 5


async def _extract_text_from_file(file: UploadFile) -> str:
    """Extract text content from uploaded file.

    For PDF/DOCX, a production implementation would use libraries like
    PyPDF2 or python-docx. This implementation handles text extraction
    for supported formats.
    """
    content = await file.read()

    content_type = file.content_type or ""
    if content_type == "text/plain":
        return content.decode("utf-8", errors="replace")

    if content_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        # Extract text from DOCX using python-docx
        try:
            from docx import Document

            doc = Document(io.BytesIO(content))
            paragraphs = [para.text for para in doc.paragraphs if para.text.strip()]
            return "\n".join(paragraphs)
        except Exception as e:
            logger.error("Failed to parse DOCX: %s", str(e))
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Failed to extract text from DOCX file.",
            )

    if content_type == "application/pdf":
        # For PDF extraction, decode as text (simplified)
        # Production would use PyPDF2 or pdfplumber
        try:
            text = content.decode("utf-8", errors="replace")
            # If it looks like binary PDF, return a placeholder message
            if text.startswith("%PDF"):
                # In production: use PyPDF2/pdfplumber for extraction
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="PDF text extraction requires PyPDF2. Please paste text directly.",
                )
            return text
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Failed to parse PDF: %s", str(e))
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Failed to extract text from PDF file.",
            )

    raise HTTPException(
        status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
        detail=f"Unsupported file type: {content_type}",
    )


@router.post("/upload", response_model=ResumeUploadResponse)
async def upload_resume(
    file: Annotated[UploadFile, File(description="Resume file (PDF, DOCX, or TXT)")],
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[dict, Depends(get_current_user)],
) -> ResumeUploadResponse:
    """Upload a resume file for analysis.

    Accepts PDF, DOCX, and TXT files up to 5MB. Extracts text content
    and stores the resume for later analysis.
    """
    user_id = uuid.UUID(user["user_id"])

    # Validate content type
    content_type = file.content_type or ""
    if content_type not in _ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported file type. Allowed: PDF, DOCX, TXT.",
        )

    # Validate file size
    file.file.seek(0, 2)
    size = file.file.tell()
    file.file.seek(0)
    if size > _MAX_FILE_SIZE_MB * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Maximum size: {_MAX_FILE_SIZE_MB}MB.",
        )

    # Extract text
    raw_text = await _extract_text_from_file(file)

    if len(raw_text.strip()) < 50:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Extracted text is too short. Please ensure the file has content.",
        )

    file_format = _ALLOWED_CONTENT_TYPES[content_type]

    resume = Resume(
        user_id=user_id,
        original_filename=file.filename,
        file_format=file_format,
        raw_text=raw_text,
    )
    db.add(resume)
    await db.flush()

    logger.info("Resume uploaded: %s (format=%s, user=%s)", resume.id, file_format, user_id)

    return ResumeUploadResponse(
        resume_id=resume.id,
        raw_text_preview=raw_text[:200],
    )


@router.post("/text", response_model=ResumeUploadResponse)
async def submit_resume_text(
    body: ResumeTextInput,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[dict, Depends(get_current_user)],
) -> ResumeUploadResponse:
    """Submit resume content as pasted text.

    Useful when the user has plain text resume content available.
    """
    user_id = uuid.UUID(user["user_id"])

    resume = Resume(
        user_id=user_id,
        file_format="txt",
        raw_text=body.text,
    )
    db.add(resume)
    await db.flush()

    logger.info("Resume text submitted: %s (user=%s)", resume.id, user_id)

    return ResumeUploadResponse(
        resume_id=resume.id,
        raw_text_preview=body.text[:200],
    )


@router.get("", response_model=list[ResumeListItem])
async def list_resumes(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[dict, Depends(get_current_user)],
) -> list[ResumeListItem]:
    """List all resumes for the current user.

    Returns resumes ordered by creation date (newest first).
    """
    user_id = uuid.UUID(user["user_id"])

    result = await db.execute(
        select(Resume)
        .where(Resume.user_id == user_id)
        .order_by(Resume.created_at.desc())
    )
    resumes = result.scalars().all()

    return [
        ResumeListItem(
            resume_id=r.id,
            original_filename=r.original_filename,
            file_format=r.file_format,
            created_at=r.created_at,
        )
        for r in resumes
    ]


@router.post("/{resume_id}/versions", status_code=status.HTTP_201_CREATED)
async def save_resume_version(
    resume_id: uuid.UUID,
    body: ResumeVersionCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[dict, Depends(get_current_user)],
) -> dict:
    """Save a resume to a named version slot.

    Supports up to 3 slots per user: fresher, experienced, domain_specific.
    Overwrites the existing version in that slot if present.
    """
    user_id = uuid.UUID(user["user_id"])

    # Verify resume exists and belongs to user
    result = await db.execute(
        select(Resume).where(Resume.id == resume_id, Resume.user_id == user_id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found.",
        )

    # Check if version slot already exists — update if so
    result = await db.execute(
        select(ResumeVersion).where(
            ResumeVersion.user_id == user_id,
            ResumeVersion.label == body.label,
        )
    )
    existing_version = result.scalar_one_or_none()

    if existing_version:
        existing_version.resume_id = resume_id
        existing_version.is_active = True
    else:
        # Check max 3 versions
        count_result = await db.execute(
            select(func.count()).select_from(ResumeVersion).where(
                ResumeVersion.user_id == user_id
            )
        )
        count = count_result.scalar() or 0
        if count >= 3:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Maximum of 3 resume versions allowed.",
            )

        version = ResumeVersion(
            user_id=user_id,
            resume_id=resume_id,
            label=body.label,
        )
        db.add(version)

    await db.flush()
    return {"message": f"Resume saved as '{body.label}' version."}


@router.get("/versions")
async def list_resume_versions(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[dict, Depends(get_current_user)],
) -> list[dict]:
    """List all resume version slots for the current user."""
    user_id = uuid.UUID(user["user_id"])

    result = await db.execute(
        select(ResumeVersion)
        .where(ResumeVersion.user_id == user_id)
        .order_by(ResumeVersion.created_at.desc())
    )
    versions = result.scalars().all()

    return [
        {
            "version_id": str(v.id),
            "resume_id": str(v.resume_id),
            "label": v.label,
            "is_active": v.is_active,
            "created_at": v.created_at.isoformat(),
        }
        for v in versions
    ]
