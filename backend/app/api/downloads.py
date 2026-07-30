"""Download API routes for generated artifacts.

Provides endpoints to download generated documents:
- GET /downloads/{run_id}/resume-docx
- GET /downloads/{run_id}/resume-pdf
- GET /downloads/{run_id}/cover-letter-docx
- GET /downloads/{run_id}/interview-pdf
- GET /downloads/{run_id}/all (ZIP bundle)
"""

import io
import logging
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db
from app.models.db import GeneratedArtifact, MatchResult
from app.schemas.cover_letter import CoverLetter
from app.schemas.interview import InterviewGuide
from app.schemas.tailored import TailoredResume

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/downloads", tags=["downloads"])


async def _get_match_result(
    run_id: uuid.UUID, user_id: uuid.UUID, db: AsyncSession
) -> MatchResult:
    """Fetch and verify a match result belongs to the user."""
    result = await db.execute(
        select(MatchResult).where(
            MatchResult.run_id == run_id,
            MatchResult.user_id == user_id,
        )
    )
    match_result = result.scalar_one_or_none()
    if not match_result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis run not found.",
        )
    if match_result.status not in ("completed", "partial"):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Analysis is not yet completed. Please wait for completion.",
        )
    return match_result


def _generate_resume_docx(match_result: MatchResult, template_id: str = "ats_classic") -> bytes:
    """Generate resume DOCX using the CV template renderer."""
    from app.agents.cv_templates import generate_cv_docx

    if not match_result.tailored_resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No tailored resume available for this run.",
        )

    tailored = TailoredResume.model_validate(match_result.tailored_resume)
    candidate_name = "Candidate"
    contact_info: dict = {}
    if match_result.parsed_resume:
        parsed = match_result.parsed_resume
        candidate_name = parsed.get("candidate_name") or "Candidate"
        ci = parsed.get("contact_info") or {}
        contact_info = {
            "designation": parsed.get("current_title") or "",
            "email": ci.get("email") or "",
            "phone": ci.get("phone") or "",
            "location": ci.get("location") or "",
            "linkedin_url": ci.get("linkedin_url") or "",
        }

    return generate_cv_docx(tailored, template_id, candidate_name, contact_info)


def _generate_cover_letter_docx(match_result: MatchResult) -> bytes:
    """Generate cover letter DOCX from stored data."""
    from app.agents.package_generation import PackageGenerationAgent

    if not match_result.cover_letter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No cover letter available for this run.",
        )

    cover_letter = CoverLetter.model_validate(match_result.cover_letter)
    candidate_name = "Candidate"
    if match_result.parsed_resume and match_result.parsed_resume.get("candidate_name"):
        candidate_name = match_result.parsed_resume["candidate_name"]

    agent = PackageGenerationAgent()
    return agent._generate_cover_letter_docx(cover_letter, candidate_name)


def _generate_interview_docx(match_result: MatchResult) -> bytes:
    """Generate interview guide DOCX from stored data."""
    from app.agents.package_generation import PackageGenerationAgent

    if not match_result.interview_guide:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No interview guide available for this run.",
        )

    guide = InterviewGuide.model_validate(match_result.interview_guide)
    candidate_name = "Candidate"
    if match_result.parsed_resume and match_result.parsed_resume.get("candidate_name"):
        candidate_name = match_result.parsed_resume["candidate_name"]

    agent = PackageGenerationAgent()
    return agent._generate_interview_guide_docx(guide, candidate_name)


@router.get("/{run_id}/resume-docx")
async def download_resume_docx(
    run_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[dict, Depends(get_current_user)],
) -> StreamingResponse:
    """Download the tailored resume as a DOCX file."""
    user_id = uuid.UUID(user["user_id"])
    match_result = await _get_match_result(run_id, user_id, db)

    docx_bytes = _generate_resume_docx(match_result)

    return StreamingResponse(
        io.BytesIO(docx_bytes),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={
            "Content-Disposition": f'attachment; filename="resume_tailored_{run_id}.docx"'
        },
    )


@router.get("/{run_id}/resume-pdf")
async def download_resume_pdf(
    run_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[dict, Depends(get_current_user)],
) -> StreamingResponse:
    """Download the tailored resume as a PDF file.

    Note: Generates DOCX internally. For true PDF conversion,
    a production deployment would use a PDF converter service.
    """
    user_id = uuid.UUID(user["user_id"])
    match_result = await _get_match_result(run_id, user_id, db)

    # Generate DOCX (PDF conversion would happen in production via LibreOffice/wkhtmltopdf)
    docx_bytes = _generate_resume_docx(match_result)

    # For now, serve the DOCX with PDF content-type note
    # In production, convert using unoconv or similar
    return StreamingResponse(
        io.BytesIO(docx_bytes),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={
            "Content-Disposition": f'attachment; filename="resume_tailored_{run_id}.docx"',
            "X-Note": "PDF conversion not available; serving DOCX format.",
        },
    )


@router.get("/{run_id}/cover-letter-docx")
async def download_cover_letter_docx(
    run_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[dict, Depends(get_current_user)],
) -> StreamingResponse:
    """Download the generated cover letter as a DOCX file."""
    user_id = uuid.UUID(user["user_id"])
    match_result = await _get_match_result(run_id, user_id, db)

    docx_bytes = _generate_cover_letter_docx(match_result)

    return StreamingResponse(
        io.BytesIO(docx_bytes),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={
            "Content-Disposition": f'attachment; filename="cover_letter_{run_id}.docx"'
        },
    )


@router.get("/{run_id}/interview-pdf")
async def download_interview_guide(
    run_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[dict, Depends(get_current_user)],
) -> StreamingResponse:
    """Download the interview preparation guide as a DOCX file."""
    user_id = uuid.UUID(user["user_id"])
    match_result = await _get_match_result(run_id, user_id, db)

    docx_bytes = _generate_interview_docx(match_result)

    return StreamingResponse(
        io.BytesIO(docx_bytes),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={
            "Content-Disposition": f'attachment; filename="interview_guide_{run_id}.docx"'
        },
    )


@router.get("/{run_id}/all")
async def download_all_zip(
    run_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[dict, Depends(get_current_user)],
) -> StreamingResponse:
    """Download all generated documents as a ZIP bundle."""
    import zipfile

    user_id = uuid.UUID(user["user_id"])
    match_result = await _get_match_result(run_id, user_id, db)

    # Generate all documents
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        if match_result.tailored_resume:
            try:
                resume_docx = _generate_resume_docx(match_result)
                zf.writestr("resume_tailored.docx", resume_docx)
            except Exception:
                pass

        if match_result.cover_letter:
            try:
                cover_docx = _generate_cover_letter_docx(match_result)
                zf.writestr("cover_letter.docx", cover_docx)
            except Exception:
                pass

        if match_result.interview_guide:
            try:
                interview_docx = _generate_interview_docx(match_result)
                zf.writestr("interview_guide.docx", interview_docx)
            except Exception:
                pass

    buffer.seek(0)

    return StreamingResponse(
        buffer,
        media_type="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="resumejdmatch_package_{run_id}.zip"'
        },
    )
