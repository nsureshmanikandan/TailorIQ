"""Tailored resume output schema - lenient for LLM output."""

from typing import Any, Optional

from pydantic import BaseModel, model_validator


class TailoredSection(BaseModel):
    """A single section of the tailored resume with change tracking."""

    section_name: str = ""
    content: str = ""
    changes_made: list[str] = []
    keywords_added: list[str] = []
    source_citations: list[Any] = []

    @model_validator(mode="before")
    @classmethod
    def coerce(cls, data):
        if isinstance(data, str):
            return {"content": data}
        if isinstance(data, dict):
            for f in ("section_name", "content"):
                if data.get(f) is None:
                    data[f] = ""
            for field in ("changes_made", "keywords_added"):
                if field in data and isinstance(data[field], list):
                    data[field] = [str(x) if not isinstance(x, str) else x for x in data[field]]
            if "name" in data and "section_name" not in data:
                data["section_name"] = data.pop("name")
            if "title" in data and "section_name" not in data:
                data["section_name"] = data.pop("title")
            # Coerce source_citations dict → list
            val = data.get("source_citations")
            if isinstance(val, dict):
                data["source_citations"] = list(val.values())
        return data


class TailoredResume(BaseModel):
    """Complete tailored resume output from the tailoring agent."""

    sections: list[TailoredSection] = []
    full_text: str = ""
    keywords_added: list[str] = []
    keywords_matched: list[str] = []
    factual_claims: list[Any] = []
    format_type: str = "ats_safe"

    @model_validator(mode="before")
    @classmethod
    def normalize(cls, data):
        if not isinstance(data, dict):
            return data
        # None coercion for top-level string fields
        if data.get("full_text") is None:
            data["full_text"] = ""
        if data.get("format_type") is None:
            data["format_type"] = "ats_safe"
        # If LLM returns sections as dict, convert to list
        if "sections" in data and isinstance(data["sections"], dict):
            data["sections"] = list(data["sections"].values())
        # Coerce string lists
        for field in ("keywords_added", "keywords_matched"):
            if field in data and isinstance(data[field], list):
                data[field] = [str(x) if not isinstance(x, str) else x for x in data[field]]
        # Coerce factual_claims dict → list
        val = data.get("factual_claims")
        if isinstance(val, dict):
            data["factual_claims"] = list(val.values())

        # Detect pattern where LLM put section names in the content field and left
        # section_name null. All sections have empty/missing section_name but short
        # single-line content that looks like a title.
        if data.get("sections"):
            sections = data["sections"]
            if isinstance(sections, list) and sections:
                all_no_name = all(
                    isinstance(s, dict) and not s.get("section_name")
                    for s in sections
                )
                all_content_short = all(
                    isinstance(s, dict) and (
                        not s.get("content")
                        or (
                            len(s.get("content", "").strip()) <= 70
                            and "\n" not in s.get("content", "")
                        )
                    )
                    for s in sections
                )
                if all_no_name and all_content_short:
                    for s in sections:
                        if isinstance(s, dict) and s.get("content") and not s.get("section_name"):
                            s["section_name"] = s.pop("content")
                            s["content"] = ""

        # If full_text missing but sections present, build it
        if not data.get("full_text") and data.get("sections"):
            sections = data["sections"]
            if isinstance(sections, list):
                parts = []
                for s in sections:
                    if isinstance(s, dict):
                        parts.append(s.get("content", ""))
                    elif isinstance(s, str):
                        parts.append(s)
                data["full_text"] = "\n\n".join(parts)
        return data
