"""Pydantic request/response schemas for the ResumeJDMatch AI API layer."""

from app.schemas.analysis import (
    AnalysisResultResponse,
    AnalysisRunRequest,
    AnalysisStatusResponse,
)
from app.schemas.auth import (
    LoginRequest,
    PasswordResetRequest,
    RegisterRequest,
    TokenResponse,
)
from app.schemas.cover_letter import CoverLetter
from app.schemas.interview import InterviewGuide, InterviewQuestion
from app.schemas.jd_parsed import JDSkill, ParsedJD
from app.schemas.job import JDResponse, JDTextInput, JDUrlInput
from app.schemas.resume import (
    ResumeListItem,
    ResumeTextInput,
    ResumeUploadResponse,
    ResumeVersionCreate,
)
from app.schemas.resume_parsed import (
    Certification,
    Education,
    Experience,
    ParsedResume,
    Skill,
)
from app.schemas.scoring import CategoryScore, GapItem, GapReport, ScoreOutput
from app.schemas.tailored import TailoredResume, TailoredSection

__all__ = [
    # Auth
    "RegisterRequest",
    "LoginRequest",
    "TokenResponse",
    "PasswordResetRequest",
    # Resume
    "ResumeUploadResponse",
    "ResumeTextInput",
    "ResumeVersionCreate",
    "ResumeListItem",
    # Job
    "JDTextInput",
    "JDUrlInput",
    "JDResponse",
    # Analysis
    "AnalysisRunRequest",
    "AnalysisStatusResponse",
    "AnalysisResultResponse",
    # Scoring
    "CategoryScore",
    "ScoreOutput",
    "GapItem",
    "GapReport",
    # Parsed
    "Skill",
    "Experience",
    "Education",
    "Certification",
    "ParsedResume",
    "JDSkill",
    "ParsedJD",
    # Tailored
    "TailoredSection",
    "TailoredResume",
    # Cover Letter
    "CoverLetter",
    # Interview
    "InterviewQuestion",
    "InterviewGuide",
]
