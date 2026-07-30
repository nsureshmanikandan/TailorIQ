"""Analysis run request/response schemas."""

import uuid
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class AnalysisRunRequest(BaseModel):
    """Request to initiate a new analysis pipeline run."""

    resume_id: uuid.UUID
    jd_id: uuid.UUID


class AnalysisStatusResponse(BaseModel):
    """Lightweight status response for polling."""

    run_id: uuid.UUID
    status: str = Field(
        description="One of: pending, running, completed, failed, partial."
    )
    current_phase: Optional[str] = None
    progress_pct: int = Field(ge=0, le=100, default=0)


class AnalysisResultResponse(BaseModel):
    """Full analysis result including all agent outputs."""

    run_id: uuid.UUID
    status: str
    pass1_score: Optional[dict[str, Any]] = None
    pass2_score: Optional[dict[str, Any]] = None
    gap_report: Optional[dict[str, Any]] = None
    ats_report: Optional[dict[str, Any]] = None
    parsed_resume: Optional[dict[str, Any]] = None
    parsed_jd: Optional[dict[str, Any]] = None
    tailored_resume: Optional[dict[str, Any]] = None
    verification_report: Optional[dict[str, Any]] = None
    cover_letter: Optional[dict[str, Any]] = None
    interview_guide: Optional[dict[str, Any]] = None
    total_tokens_used: int = 0
    total_cost_usd: float = 0.0
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}
