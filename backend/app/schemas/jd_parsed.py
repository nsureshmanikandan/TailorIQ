"""Parsed job description schema - lenient for LLM output."""

from typing import Any, Optional

from pydantic import BaseModel, Field, model_validator


class JDSkill(BaseModel):
    """Skill requirement extracted from a job description."""

    name: str = ""
    category: str = "hard_skill"
    priority: str = "must_have"
    signal_text: str = ""

    @model_validator(mode="before")
    @classmethod
    def normalize_fields(cls, data):
        if isinstance(data, str):
            return {"name": data}
        if isinstance(data, dict):
            for f in ("name", "category", "priority", "signal_text"):
                if data.get(f) is None:
                    data[f] = ""
            if "type" in data and "category" not in data:
                data["category"] = data.pop("type")
            if "skill" in data and "name" not in data:
                data["name"] = data.pop("skill")
        return data


class ParsedJD(BaseModel):
    """Full structured representation of a parsed job description.
    
    All list fields default to empty to handle partial LLM responses.
    """

    company_name: Optional[str] = None
    role_title: str = ""
    role_title_normalized: Optional[str] = None
    seniority_level: Optional[str] = None
    seniority_indicators: list[str] = []
    must_have_skills: list[JDSkill] = []
    nice_to_have_skills: list[JDSkill] = []
    responsibilities: list[str] = []
    required_certifications: list[str] = []
    domain_requirements: list[str] = []
    ats_keywords: list[str] = []
    experience_years_required: Optional[str] = None
    original_text: str = ""
    parse_confidence: float = Field(default=0.8, ge=0.0, le=1.0)

    @model_validator(mode="before")
    @classmethod
    def normalize_fields(cls, data):
        """Handle common LLM field naming variations."""
        if isinstance(data, dict):
            mappings = {
                "skills": "must_have_skills",
                "required_skills": "must_have_skills",
                "preferred_skills": "nice_to_have_skills",
                "optional_skills": "nice_to_have_skills",
                "keywords": "ats_keywords",
            }
            for alt, canonical in mappings.items():
                if alt in data and canonical not in data:
                    data[canonical] = data.pop(alt)

            # Coerce dict → list for skill list fields
            for field in ("must_have_skills", "nice_to_have_skills"):
                val = data.get(field)
                if isinstance(val, dict):
                    data[field] = list(val.values())

            # Coerce string-list fields that LLM may return as list[dict]
            for field in ("domain_requirements", "responsibilities",
                          "required_certifications", "ats_keywords",
                          "seniority_indicators"):
                if field in data and isinstance(data[field], list):
                    data[field] = [
                        x if isinstance(x, str)
                        else x.get("name", x.get("domain", x.get("description", str(x))))
                        for x in data[field]
                    ]
                elif field in data and isinstance(data[field], dict):
                    data[field] = list(data[field].values())
        return data
