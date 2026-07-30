"""Parsed resume structured data schema - lenient for LLM output."""

from typing import Any, Optional

from pydantic import BaseModel, Field, model_validator


class Skill(BaseModel):
    """Extracted skill with provenance metadata."""

    name: str = ""
    category: str = "hard_skill"
    confidence: float = Field(default=0.8, ge=0.0, le=1.0)
    source_text: str = ""
    is_contextual: bool = False

    @model_validator(mode="before")
    @classmethod
    def coerce(cls, data):
        if isinstance(data, str):
            return {"name": data}
        if isinstance(data, dict):
            for f in ("name", "category", "source_text"):
                if data.get(f) is None:
                    data[f] = ""
            if "type" in data and "category" not in data:
                data["category"] = data.pop("type")
            if "skill" in data and "name" not in data:
                data["name"] = data.pop("skill")
        return data


class Experience(BaseModel):
    """Work experience entry."""

    job_title: str = ""
    job_title_normalized: Optional[str] = None
    employer: str = ""
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    description: str = ""
    achievements: list[str] = []
    quantifiable_metrics: list[str] = []
    experience_type: str = "full_time"
    original_text: str = ""

    @model_validator(mode="before")
    @classmethod
    def coerce(cls, data):
        if isinstance(data, str):
            return {"description": data}
        if isinstance(data, dict):
            # Coerce null → "" for required str fields
            for f in ("job_title", "employer", "description", "original_text", "experience_type"):
                if data.get(f) is None:
                    data[f] = ""
            if "title" in data and "job_title" not in data:
                data["job_title"] = data.pop("title")
            if "role" in data and "job_title" not in data:
                data["job_title"] = data.pop("role")
            if "company" in data and "employer" not in data:
                data["employer"] = data.pop("company")
            for field in ("quantifiable_metrics", "achievements"):
                if field in data and isinstance(data[field], list):
                    data[field] = [
                        str(x) if not isinstance(x, str) else x
                        for x in data[field]
                    ]
                elif field in data and isinstance(data[field], dict):
                    data[field] = list(data[field].values())
        return data


class Education(BaseModel):
    """Education entry."""

    degree: str = ""
    institution: str = ""
    graduation_date: Optional[str] = None
    field_of_study: Optional[str] = None
    original_text: str = ""

    @model_validator(mode="before")
    @classmethod
    def coerce(cls, data):
        if isinstance(data, str):
            return {"degree": data}
        if isinstance(data, dict):
            for f in ("degree", "institution", "original_text"):
                if data.get(f) is None:
                    data[f] = ""
        return data


class Certification(BaseModel):
    """Professional certification."""

    name: str = ""
    name_normalized: Optional[str] = None
    issuing_org: Optional[str] = None
    date_obtained: Optional[str] = None
    original_text: str = ""

    @model_validator(mode="before")
    @classmethod
    def coerce(cls, data):
        if isinstance(data, str):
            return {"name": data}
        if isinstance(data, dict):
            for f in ("name", "original_text"):
                if data.get(f) is None:
                    data[f] = ""
        return data


def _to_str_list(val: Any) -> list[str]:
    """Convert any value to a flat list of strings."""
    if val is None:
        return []
    if isinstance(val, str):
        return [val]
    if isinstance(val, dict):
        val = list(val.values())
    if isinstance(val, list):
        result = []
        for x in val:
            if isinstance(x, str):
                result.append(x)
            elif isinstance(x, dict):
                result.append(x.get("name", x.get("value", str(x))))
            else:
                result.append(str(x))
        return result
    return [str(val)]


class ParsedResume(BaseModel):
    """Full structured representation of a parsed resume.

    All list/dict fields default to empty to handle partial LLM responses.
    """

    candidate_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    linkedin_url: Optional[str] = None
    location: Optional[str] = None
    skills: list[Skill] = []
    experience: list[Experience] = []
    education: list[Education] = []
    certifications: list[Certification] = []
    projects: list[Any] = []
    total_years_experience: Optional[float] = None
    domain_keywords: list[str] = []
    tools_and_platforms: list[str] = []
    original_sections: dict[str, str] = {}
    parse_confidence: float = Field(default=0.8, ge=0.0, le=1.0)

    @model_validator(mode="before")
    @classmethod
    def normalize_fields(cls, data):
        """Handle common LLM field naming variations and type coercions."""
        if not isinstance(data, dict):
            return data

        # Map common alternative field names
        name_aliases = ("full_name", "name", "candidate")
        for key in name_aliases:
            if key in data and "candidate_name" not in data:
                data["candidate_name"] = data.pop(key)
                break

        field_aliases = {
            "tools": "tools_and_platforms",
            "platforms": "tools_and_platforms",
            "technologies": "tools_and_platforms",
            "work_experience": "experience",
            "jobs": "experience",
            "certs": "certifications",
            "keywords": "domain_keywords",
        }
        for alt, canonical in field_aliases.items():
            if alt in data and canonical not in data:
                data[canonical] = data.pop(alt)

        # Coerce dict → list for all array fields.
        # The LLM sometimes returns a single object instead of a list.
        for field in ("skills", "experience", "education", "certifications", "projects"):
            val = data.get(field)
            if isinstance(val, dict):
                data[field] = list(val.values())
            elif val is not None and not isinstance(val, list):
                data[field] = []

        # Coerce string list fields
        for field in ("domain_keywords", "tools_and_platforms"):
            if field in data:
                data[field] = _to_str_list(data[field])

        return data
