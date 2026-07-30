"""Cover letter output schema - lenient for LLM output."""

from typing import Any, Optional

from pydantic import BaseModel, Field, model_validator


class CoverLetter(BaseModel):
    """Generated cover letter with grounding metadata."""

    content: str = ""
    word_count: int = Field(default=300, ge=0, le=1000)
    company_name: str = ""
    role_title: str = ""
    jd_requirements_referenced: list[str] = []
    resume_evidence: list[Any] = []
    grounding_citations: list[Any] = []
    region_convention: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def normalize(cls, data):
        if isinstance(data, str) and data.strip():
            # LLM returned the cover letter as a plain string instead of JSON
            return {"content": data.strip()}
        if not isinstance(data, dict):
            return data
        # Aliases for content — try all common field names the LLM might use.
        # Check both missing and null/empty cases.
        if not data.get("content"):
            for alias in (
                "letter", "body", "text", "letter_text", "letter_body",
                "cover_letter_text", "cover_letter_body", "message", "cover_letter_content",
            ):
                if data.get(alias):
                    data["content"] = data.pop(alias)
                    break
        # Aliases for other fields
        if "company" in data and "company_name" not in data:
            data["company_name"] = data.pop("company")
        if "role" in data and "role_title" not in data:
            data["role_title"] = data.pop("role")
        # None → "" coercion for required string fields
        for f in ("content", "company_name", "role_title"):
            if data.get(f) is None:
                data[f] = ""
        # Auto-compute word_count from content
        if data.get("content") and "word_count" not in data:
            data["word_count"] = min(len(data["content"].split()), 1000)
        # Coerce string lists
        if "jd_requirements_referenced" in data and isinstance(data["jd_requirements_referenced"], list):
            data["jd_requirements_referenced"] = [
                x if isinstance(x, str) else str(x.get("requirement", x))
                for x in data["jd_requirements_referenced"]
            ]
        # Coerce list[Any] fields from dict → list
        for field in ("resume_evidence", "grounding_citations"):
            val = data.get(field)
            if isinstance(val, dict):
                data[field] = list(val.values())
        return data
