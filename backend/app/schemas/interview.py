"""Interview preparation guide output schema - lenient for LLM output."""

from typing import Any, Optional

from pydantic import BaseModel, Field, model_validator


class InterviewQuestion(BaseModel):
    """Single interview question with preparation guidance."""

    question: str = ""
    category: str = "behavioral"
    source: str = ""
    star_skeleton: Optional[dict] = None
    resume_evidence: Optional[str] = None
    is_gap_question: bool = False
    note: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def coerce(cls, data):
        if isinstance(data, str):
            return {"question": data}
        if isinstance(data, dict):
            for f in ("question", "category", "source"):
                if data.get(f) is None:
                    data[f] = ""
            if "type" in data and "category" not in data:
                data["category"] = data.pop("type")
            # star_skeleton must be a dict or None — coerce or discard
            sk = data.get("star_skeleton")
            if sk is not None and not isinstance(sk, dict):
                data["star_skeleton"] = None
            # resume_evidence and note must be str or None
            for f in ("resume_evidence", "note"):
                val = data.get(f)
                if val is not None and not isinstance(val, str):
                    data[f] = str(val) if isinstance(val, (int, float, bool)) else None
            # is_gap_question: coerce string representations
            iq = data.get("is_gap_question")
            if isinstance(iq, str):
                data["is_gap_question"] = iq.lower() in ("true", "yes", "1")
        return data


class InterviewGuide(BaseModel):
    """Complete interview preparation guide."""

    behavioral_questions: list[InterviewQuestion] = []
    technical_questions: list[InterviewQuestion] = []
    total_count: int = Field(default=0, ge=0, le=50)
    preparation_tips: list[str] = []

    @model_validator(mode="before")
    @classmethod
    def normalize(cls, data):
        if not isinstance(data, dict):
            return data
        # Aliases
        if "questions" in data and "behavioral_questions" not in data:
            # Split questions by category if given as flat list
            questions = data.pop("questions")
            if isinstance(questions, list):
                behavioral = []
                technical = []
                for q in questions:
                    if isinstance(q, str):
                        behavioral.append({"question": q})
                    elif isinstance(q, dict):
                        cat = q.get("category", q.get("type", "behavioral"))
                        if cat in ("technical", "domain"):
                            technical.append(q)
                        else:
                            behavioral.append(q)
                data["behavioral_questions"] = behavioral
                data["technical_questions"] = technical
        # Auto-compute total_count (clamped to field constraint)
        b_count = len(data.get("behavioral_questions", []))
        t_count = len(data.get("technical_questions", []))
        data["total_count"] = min(b_count + t_count, 50)
        # Coerce tips
        if "preparation_tips" in data and isinstance(data["preparation_tips"], list):
            data["preparation_tips"] = [
                x if isinstance(x, str) else str(x)
                for x in data["preparation_tips"]
            ]
        elif "tips" in data:
            data["preparation_tips"] = data.pop("tips")
        return data
