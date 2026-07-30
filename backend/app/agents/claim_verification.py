"""Claim verification agent — verifies factual claims in tailored resumes.

Compares every claim in the tailored resume against the original source
resume to ensure no fabricated information is included.
"""

import json
import logging
from string import Template

from pydantic import BaseModel, Field, model_validator

from app.agents.base import BaseAgent
from app.schemas.resume_parsed import ParsedResume
from app.schemas.tailored import TailoredResume
from app.services.llm_service import LLMService
from app.services.prompt_loader import PromptLoader

logger = logging.getLogger(__name__)


class VerifiedClaim(BaseModel):
    """A single verified claim."""

    claim_text: str = ""
    source_reference: str = ""
    status: str = "verified"

    @model_validator(mode="before")
    @classmethod
    def coerce(cls, data):
        if isinstance(data, str):
            return {"claim_text": data}
        if isinstance(data, dict):
            if "claim" in data and "claim_text" not in data:
                data["claim_text"] = data.pop("claim")
            if "text" in data and "claim_text" not in data:
                data["claim_text"] = data.pop("text")
            if "reference" in data and "source_reference" not in data:
                data["source_reference"] = data.pop("reference")
            if "source" in data and "source_reference" not in data:
                data["source_reference"] = data.pop("source")
            for f in ("claim_text", "source_reference", "status"):
                if data.get(f) is None:
                    data[f] = ""
        return data


class UnverifiedClaim(BaseModel):
    """A single unverified claim."""

    claim_text: str = ""
    reason: str = ""
    status: str = "unverified"

    @model_validator(mode="before")
    @classmethod
    def coerce(cls, data):
        if isinstance(data, str):
            return {"claim_text": data}
        if isinstance(data, dict):
            if "claim" in data and "claim_text" not in data:
                data["claim_text"] = data.pop("claim")
            if "text" in data and "claim_text" not in data:
                data["claim_text"] = data.pop("text")
            if "issue" in data and "reason" not in data:
                data["reason"] = data.pop("issue")
            for f in ("claim_text", "reason", "status"):
                if data.get(f) is None:
                    data[f] = ""
        return data


class VerificationReport(BaseModel):
    """Complete verification report for a tailored resume."""

    verified_claims: list[VerifiedClaim] = []
    unverified_claims: list[UnverifiedClaim] = []
    verified_resume_text: str = ""
    verification_score: float = Field(default=1.0, ge=0.0, le=1.0)
    total_claims: int = 0
    changes_made: list[str] = []

    @model_validator(mode="before")
    @classmethod
    def normalize(cls, data):
        if not isinstance(data, dict):
            return data
        if "verified_resume" in data and "verified_resume_text" not in data:
            data["verified_resume_text"] = data.pop("verified_resume")
        if "resume_text" in data and "verified_resume_text" not in data:
            data["verified_resume_text"] = data.pop("resume_text")
        if data.get("verified_resume_text") is None:
            data["verified_resume_text"] = ""
        if "score" in data and "verification_score" not in data:
            data["verification_score"] = data.pop("score")
        if "changes" in data and "changes_made" not in data:
            data["changes_made"] = data.pop("changes")
        # Flat "claims" list → split by status
        if "claims" in data and "verified_claims" not in data:
            claims = data.pop("claims")
            if isinstance(claims, list):
                data["verified_claims"] = [
                    c for c in claims
                    if isinstance(c, dict) and c.get("status") == "verified"
                ]
                data["unverified_claims"] = [
                    c for c in claims
                    if isinstance(c, dict) and c.get("status") != "verified"
                ]
        for field in ("verified_claims", "unverified_claims"):
            val = data.get(field)
            if isinstance(val, dict):
                data[field] = list(val.values())
            elif val is not None and not isinstance(val, list):
                data[field] = []
        if "changes_made" in data and isinstance(data["changes_made"], list):
            data["changes_made"] = [str(x) if not isinstance(x, str) else x for x in data["changes_made"]]
        if "verification_score" in data:
            try:
                data["verification_score"] = max(0.0, min(1.0, float(data["verification_score"])))
            except (ValueError, TypeError):
                data["verification_score"] = 1.0
        if "total_claims" not in data:
            data["total_claims"] = (
                len(data.get("verified_claims", []))
                + len(data.get("unverified_claims", []))
            )
        return data


class ClaimVerificationInput(BaseModel):
    """Input schema for the claim verification agent."""

    tailored_resume: TailoredResume
    original_resume: ParsedResume
    source_text: str  # Original raw resume text


class ClaimVerificationAgent(BaseAgent[ClaimVerificationInput, VerificationReport]):
    """Verifies factual claims in tailored resumes against the source.

    Ensures no fabricated skills, metrics, or experiences are present.
    Removes unverified claims from the output resume text.
    """

    agent_name = "claim_verification"
    max_output_tokens = 5000
    temperature = 0.1

    def __init__(
        self,
        llm_service: LLMService,
        prompt_loader: PromptLoader,
    ) -> None:
        super().__init__(llm_service=llm_service, prompt_loader=prompt_loader)

    async def execute(self, input_data: ClaimVerificationInput) -> VerificationReport:
        """Verify all factual claims in a tailored resume.

        Args:
            input_data: Tailored resume, original parsed resume, and source text.

        Returns:
            VerificationReport with verified resume and claim audit.
        """
        templates = self._load_prompt_template()
        system_prompt = templates["system_prompt"]

        tailored_json = input_data.tailored_resume.model_dump_json(indent=2)
        original_resume_json = input_data.original_resume.model_dump_json(indent=2)

        user_template = Template(templates["user_prompt_template"])
        user_prompt = user_template.safe_substitute(
            tailored_json=tailored_json,
            original_resume_json=original_resume_json,
            source_text=input_data.source_text,
        )

        response_schema = VerificationReport.model_json_schema()

        response = await self._call_llm(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            response_schema=response_schema,
        )

        report = VerificationReport.model_validate(response.content)

        # Validate total_claims matches sum of verified + unverified
        expected_total = len(report.verified_claims) + len(report.unverified_claims)
        if report.total_claims != expected_total:
            logger.info(
                "Correcting total_claims from %d to %d",
                report.total_claims,
                expected_total,
            )
            report.total_claims = expected_total

        # Validate verification_score
        if report.total_claims > 0:
            expected_score = len(report.verified_claims) / report.total_claims
            if abs(report.verification_score - expected_score) > 0.05:
                logger.info(
                    "Correcting verification_score from %.2f to %.2f",
                    report.verification_score,
                    expected_score,
                )
                report.verification_score = round(expected_score, 4)

        is_valid = await self.validate_output(report)
        if not is_valid:
            logger.warning("Claim verification output failed validation, returning as-is")

        return report
