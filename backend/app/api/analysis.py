"""Analysis API routes for running and querying pipeline results.

Provides endpoints to:
- POST /analysis/run — Start a new analysis pipeline (returns 202 Accepted)
- GET /analysis/{run_id} — Get full analysis results
- GET /analysis/{run_id}/status — Get status and progress
- GET /analysis/{run_id}/cv-download — Download CV DOCX in selected template
"""

import logging
import uuid
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings, get_settings
from app.dependencies import get_current_user, get_db
from app.models.db import JobDescription, MatchResult, Resume
from app.orchestrator.pipeline import PipelineOrchestrator
from app.schemas.analysis import (
    AnalysisResultResponse,
    AnalysisRunRequest,
    AnalysisStatusResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analysis", tags=["analysis"])


# Phase progress mapping for progress_pct calculation
_PHASE_PROGRESS = {
    "pending": 0,
    "phase_1": 10,
    "phase_2": 30,
    "phase_3": 55,
    "phase_4": 75,
    "phase_5": 90,
    "completed": 100,
    "partial": 100,
    "failed": 100,
}


async def _run_pipeline(
    resume_id: uuid.UUID,
    jd_id: uuid.UUID,
    user_id: uuid.UUID,
    run_id: uuid.UUID,
    settings: Settings,
) -> None:
    """Background task to execute the analysis pipeline.

    Creates its own database session since background tasks run
    outside the request lifecycle.
    """
    from app.dependencies import _get_session_factory

    factory = _get_session_factory(settings)
    async with factory() as db:
        try:
            from app.services.llm_service import LLMService
            from app.services.prompt_loader import PromptLoader

            llm_service = LLMService(settings)
            prompt_loader = PromptLoader()
            orchestrator = PipelineOrchestrator(
                db=db,
                llm_service=llm_service,
                prompt_loader=prompt_loader,
            )
            await orchestrator.run(
                resume_id=resume_id,
                jd_id=jd_id,
                user_id=user_id,
                run_id=run_id,
            )
            # Each phase already committed its own data; nothing left to commit here.
        except Exception as e:
            logger.exception("Pipeline background task failed for run %s", run_id)
            # Update status to failed — use a fresh begin() after any rollback
            try:
                from sqlalchemy import update

                await db.execute(
                    update(MatchResult)
                    .where(MatchResult.run_id == run_id)
                    .values(status="failed")
                )
                await db.commit()
            except Exception:
                pass


@router.post(
    "/run",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=AnalysisStatusResponse,
)
async def start_analysis(
    body: AnalysisRunRequest,
    background_tasks: BackgroundTasks,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[dict, Depends(get_current_user)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> AnalysisStatusResponse:
    """Start a new analysis pipeline run.

    Creates a MatchResult record and launches the pipeline in the background.
    Returns immediately with a run_id for status polling.
    """
    user_id = uuid.UUID(user["user_id"])

    # Verify resume belongs to user
    result = await db.execute(
        select(Resume).where(Resume.id == body.resume_id, Resume.user_id == user_id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found or does not belong to you.",
        )

    # Verify JD belongs to user
    result = await db.execute(
        select(JobDescription).where(
            JobDescription.id == body.jd_id, JobDescription.user_id == user_id
        )
    )
    if not result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job description not found or does not belong to you.",
        )

    # Create MatchResult record
    run_id = uuid.uuid4()
    match_result = MatchResult(
        user_id=user_id,
        resume_id=body.resume_id,
        jd_id=body.jd_id,
        run_id=run_id,
        status="pending",
    )
    db.add(match_result)
    await db.flush()

    # Launch pipeline in background
    background_tasks.add_task(
        _run_pipeline,
        resume_id=body.resume_id,
        jd_id=body.jd_id,
        user_id=user_id,
        run_id=run_id,
        settings=settings,
    )

    logger.info("Analysis started: run_id=%s, user=%s", run_id, user_id)

    return AnalysisStatusResponse(
        run_id=run_id,
        status="pending",
        current_phase="queued",
        progress_pct=0,
    )


@router.get("/{run_id}", response_model=AnalysisResultResponse)
async def get_analysis_results(
    run_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[dict, Depends(get_current_user)],
) -> AnalysisResultResponse:
    """Get full analysis results for a completed run.

    Returns all agent outputs including scores, gap report,
    tailored resume, cover letter, and interview guide.
    """
    user_id = uuid.UUID(user["user_id"])

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

    return AnalysisResultResponse(
        run_id=match_result.run_id,
        status=match_result.status,
        pass1_score=match_result.pass1_score,
        pass2_score=match_result.pass2_score,
        gap_report=match_result.gap_report,
        ats_report=match_result.ats_report,
        parsed_resume=match_result.parsed_resume,
        parsed_jd=match_result.parsed_jd,
        tailored_resume=match_result.tailored_resume,
        verification_report=match_result.verification_report,
        cover_letter=match_result.cover_letter,
        interview_guide=match_result.interview_guide,
        total_tokens_used=match_result.total_tokens_used,
        total_cost_usd=float(match_result.total_cost_usd),
        started_at=match_result.started_at,
        completed_at=match_result.completed_at,
        created_at=match_result.created_at,
    )


@router.get("/{run_id}/status", response_model=AnalysisStatusResponse)
async def get_analysis_status(
    run_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[dict, Depends(get_current_user)],
) -> AnalysisStatusResponse:
    """Get lightweight status and progress for an analysis run.

    Used for polling during pipeline execution.
    """
    user_id = uuid.UUID(user["user_id"])

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

    # Determine current phase from populated fields
    current_phase = _determine_phase(match_result)
    progress_pct = _PHASE_PROGRESS.get(current_phase, 0)

    if match_result.status in ("completed", "partial", "failed"):
        progress_pct = 100

    return AnalysisStatusResponse(
        run_id=match_result.run_id,
        status=match_result.status,
        current_phase=current_phase,
        progress_pct=progress_pct,
    )


def _determine_phase(match_result: MatchResult) -> str:
    """Determine the current phase based on populated result fields."""
    if match_result.status in ("completed", "partial", "failed"):
        return match_result.status

    if match_result.cover_letter or match_result.interview_guide:
        return "phase_5"
    if match_result.tailored_resume:
        return "phase_4"
    if match_result.pass1_score:
        return "phase_3"
    if match_result.parsed_resume:
        return "phase_2"
    return "phase_1"


@router.get("/{run_id}/cv-download")
async def download_cv_template(
    run_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[dict, Depends(get_current_user)],
    template: str = Query(default="ats_classic", description="CV template ID"),
) -> StreamingResponse:
    """Download the tailored CV as a DOCX in the selected template style."""
    from app.agents.cv_templates import TEMPLATE_REGISTRY, generate_cv_docx
    from app.schemas.tailored import TailoredResume

    if template not in TEMPLATE_REGISTRY:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown template '{template}'. Valid options: {list(TEMPLATE_REGISTRY)}",
        )

    user_id = uuid.UUID(user["user_id"])
    result = await db.execute(
        select(MatchResult).where(
            MatchResult.run_id == run_id,
            MatchResult.user_id == user_id,
        )
    )
    match_result = result.scalar_one_or_none()
    if not match_result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analysis run not found.")

    if match_result.status not in ("completed", "partial"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Analysis not yet complete. Wait for the pipeline to finish.",
        )

    if not match_result.tailored_resume:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tailored resume not available for this run.",
        )

    # Extract candidate info from the raw parsed_resume JSON.
    # ParsedResume uses flat top-level fields (not a nested contact_info).
    # LinkedIn and designation are extracted with regex fallbacks from full_text
    # because the LLM sometimes omits them from the structured schema fields.
    import re as _re
    candidate_name = "Candidate"
    contact_info: dict = {}
    full_text_for_header = ""
    if match_result.tailored_resume:
        full_text_for_header = (match_result.tailored_resume.get("full_text") or "")
    if match_result.parsed_resume:
        try:
            raw = match_result.parsed_resume  # already a dict stored as JSON
            candidate_name = raw.get("candidate_name") or "Candidate"

            # LinkedIn: flat schema field first, then regex from full_text
            linkedin = raw.get("linkedin_url") or raw.get("linkedin") or ""
            if not linkedin and full_text_for_header:
                m = _re.search(r'linkedin\.com/in/[\w-]+', full_text_for_header, _re.IGNORECASE)
                if m:
                    linkedin = m.group(0)

            # Designation: pull Target Title / Target Role line from full_text preamble
            # (ParsedResume has no current_title field — this info only lives in full_text)
            designation = raw.get("current_title") or raw.get("designation") or ""
            if not designation and full_text_for_header:
                for line in full_text_for_header.split("\n")[:15]:
                    stripped = line.strip()
                    if _re.match(
                        r'^(Target\s+(?:Title|Role)|Seeking|Current\s+Title|Designation)\s*[:\-]',
                        stripped,
                        _re.IGNORECASE,
                    ):
                        designation = stripped
                        break

            contact_info = {
                "location": raw.get("location") or "",
                "email": raw.get("email") or "",
                "phone": raw.get("phone") or "",
                "linkedin": linkedin,
                "designation": designation,
            }
        except Exception:
            logger.warning("Could not extract contact info for run %s — using defaults", run_id)

    try:
        tailored = TailoredResume.model_validate(match_result.tailored_resume)
        docx_bytes = generate_cv_docx(tailored, template, candidate_name, contact_info)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception:
        logger.exception("CV DOCX generation failed for run %s template %s", run_id, template)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="CV generation failed. Please try again.",
        )

    safe_name = candidate_name.replace(" ", "_").lower()
    filename = f"{safe_name}_cv_{template}.docx"

    import io
    return StreamingResponse(
        io.BytesIO(docx_bytes),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
