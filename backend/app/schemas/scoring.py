"""Scoring and gap analysis output schemas - lenient for LLM output."""

from typing import Any, Optional

from pydantic import BaseModel, Field, model_validator


class CategoryScore(BaseModel):
    """Individual scoring category with weight and reasoning."""

    category: str = ""
    score: int = Field(default=0, ge=0, le=100)
    weight: float = 0.25
    reasoning: str = ""
    matched_items: list[str] = []
    missing_items: list[str] = []

    # Actual scoring weights used in the pipeline
    _WEIGHTS: dict = {
        "technical_skills": 0.40,
        "experience_relevance": 0.20,
        "domain_certifications": 0.25,
        "achievement_alignment": 0.15,
    }

    @model_validator(mode="before")
    @classmethod
    def coerce(cls, data):
        if isinstance(data, dict):
            for f in ("category", "reasoning"):
                if data.get(f) is None:
                    data[f] = ""
            # Override weight with the actual pipeline weight so the UI shows correct %
            cat = data.get("category", "")
            actual_weights = {
                "technical_skills": 0.40,
                "experience_relevance": 0.20,
                "domain_certifications": 0.25,
                "achievement_alignment": 0.15,
            }
            if cat in actual_weights:
                data["weight"] = actual_weights[cat]
            # Coerce matched/missing items from dicts to strings
            for field in ("matched_items", "missing_items"):
                if field in data and isinstance(data[field], list):
                    data[field] = [
                        x if isinstance(x, str) else str(x.get("name", x.get("skill", x)))
                        for x in data[field]
                    ]
            # Clamp score
            if "score" in data:
                try:
                    data["score"] = max(0, min(100, int(data["score"])))
                except (ValueError, TypeError):
                    data["score"] = 0
        return data


class ScoreOutput(BaseModel):
    """Complete match scoring output from the scoring agent."""

    model_config = {"protected_namespaces": ()}

    overall_score: int = Field(default=0, ge=0, le=100)
    category_scores: list[CategoryScore] = []
    matched_keywords: list[str] = []
    missing_keywords: list[str] = []
    skills_gap: list[str] = []
    certification_gap: list[str] = []
    achievement_gap: list[str] = []
    semantic_matches: list[Any] = []
    scoring_seed: int = 42
    model_version: str = ""

    @model_validator(mode="before")
    @classmethod
    def normalize(cls, data):
        if not isinstance(data, dict):
            return data

        # overall_score aliases — LLM may return "score", "total_score", etc.
        for alias in ("score", "total_score", "match_score", "final_score", "composite_score"):
            if alias in data and "overall_score" not in data:
                data["overall_score"] = data.pop(alias)
                break

        # category_scores: LLM often returns {"technical_skills": 88, ...} instead of a list
        cat = data.get("category_scores")
        if isinstance(cat, dict):
            data["category_scores"] = [
                {"category": k, **v} if isinstance(v, dict) else {"category": k, "score": v}
                for k, v in cat.items()
            ]

        # semantic_matches: LLM often returns {"Azure": ["Microsoft Azure", ...]} instead of a list
        sm = data.get("semantic_matches")
        if isinstance(sm, dict):
            data["semantic_matches"] = [{"term": k, "matches": v} for k, v in sm.items()]

        # Coerce keyword list fields from dicts or mixed types to string lists
        for field in ("matched_keywords", "missing_keywords", "skills_gap",
                      "certification_gap", "achievement_gap"):
            val = data.get(field)
            if val is None:
                continue
            if isinstance(val, dict):
                # {"k1": "Python", "k2": "Azure"} → ["Python", "Azure"]
                data[field] = [v if isinstance(v, str) else str(v) for v in val.values()]
            elif isinstance(val, list):
                data[field] = [
                    x if isinstance(x, str) else str(x.get("name", x.get("keyword", x)))
                    for x in val
                ]
            else:
                data[field] = []

        # Clamp overall_score
        if "overall_score" in data:
            try:
                data["overall_score"] = max(0, min(100, int(data["overall_score"])))
            except (ValueError, TypeError):
                data["overall_score"] = 0
        return data


class GapItem(BaseModel):
    """Single identified gap between resume and JD."""

    gap_type: str = ""
    description: str = ""
    severity: str = "recommended"
    jd_requirement_ref: str = ""
    suggestion: str = ""
    is_transferable: bool = False

    @model_validator(mode="before")
    @classmethod
    def coerce(cls, data):
        if isinstance(data, str):
            return {"description": data}
        if isinstance(data, dict):
            for f in ("gap_type", "description", "severity", "jd_requirement_ref", "suggestion"):
                if data.get(f) is None:
                    data[f] = ""
            # Normalize severity
            sev = data.get("severity", "recommended")
            if sev not in ("critical", "recommended"):
                data["severity"] = "recommended"
        return data


class GapReport(BaseModel):
    """Complete gap analysis report."""

    gaps: list[GapItem] = []
    critical_count: int = 0
    recommended_count: int = 0
    coverage_percentage: float = Field(default=0.0, ge=0.0, le=100.0)
    summary: str = ""

    @model_validator(mode="before")
    @classmethod
    def normalize(cls, data):
        if isinstance(data, dict):
            if "gaps" in data and isinstance(data["gaps"], dict):
                data["gaps"] = list(data["gaps"].values())
            # Clamp coverage
            if "coverage_percentage" in data:
                try:
                    data["coverage_percentage"] = max(0.0, min(100.0, float(data["coverage_percentage"])))
                except (ValueError, TypeError):
                    data["coverage_percentage"] = 0.0
            # Auto-compute counts from the gaps list if not provided
            gaps = data.get("gaps", [])
            if isinstance(gaps, list):
                if "critical_count" not in data:
                    data["critical_count"] = sum(
                        1 for g in gaps
                        if isinstance(g, dict) and g.get("severity") == "critical"
                    )
                if "recommended_count" not in data:
                    data["recommended_count"] = sum(
                        1 for g in gaps
                        if isinstance(g, dict) and g.get("severity") == "recommended"
                    )
        return data
