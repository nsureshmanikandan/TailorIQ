"""Job description request/response schemas."""

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, HttpUrl


class JDTextInput(BaseModel):
    """Job description text input."""

    text: str = Field(
        ...,
        min_length=50,
        max_length=50000,
        description="Raw job description text.",
    )


class JDUrlInput(BaseModel):
    """Job description URL input for scraping."""

    url: HttpUrl = Field(description="URL of the job posting to fetch.")


class JDResponse(BaseModel):
    """Job description creation response."""

    jd_id: uuid.UUID
    raw_text: str
    source_type: str
    source_url: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}
