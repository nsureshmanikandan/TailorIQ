"""Resume-related request/response schemas."""

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ResumeUploadResponse(BaseModel):
    """Response after successful resume upload."""

    resume_id: uuid.UUID
    raw_text_preview: str = Field(
        description="First 200 characters of extracted text."
    )


class ResumeTextInput(BaseModel):
    """Resume text paste input."""

    text: str = Field(
        ...,
        min_length=50,
        max_length=50000,
        description="Raw resume text content.",
    )


class ResumeVersionCreate(BaseModel):
    """Request to save a resume as a named version slot."""

    label: str = Field(
        ...,
        pattern=r"^(fresher|experienced|domain_specific)$",
        description="Version label: fresher, experienced, or domain_specific.",
    )


class ResumeListItem(BaseModel):
    """Resume summary for list responses."""

    resume_id: uuid.UUID
    original_filename: Optional[str] = None
    file_format: str
    created_at: datetime

    model_config = {"from_attributes": True}
