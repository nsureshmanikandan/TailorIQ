"""ATS compatibility check agent — analyzes resume formatting for ATS systems.

Identifies formatting, structural, and content issues that could cause
problems with Applicant Tracking System parsers.
"""

import json
import logging
from string import Template
from typing import Optional

from pydantic import BaseModel, Field, model_validator

from app.agents.base import BaseAgent
from app.services.llm_service import LLMService
from app.services.prompt_loader import PromptLoader

logger = logging.getLogger(__name__)


class ATSRisk(BaseModel):
    """A single ATS compatibility risk."""

    risk_type: str = ""
    description: str = ""
    severity: str = "medium"
    location: Optional[str] = None
    remediation: str = ""

    @model_validator(mode="before")
    @classmethod
    def coerce(cls, data):
        if isinstance(data, str):
            return {"description": data}
        if isinstance(data, dict):
            for f in ("risk_type", "description", "severity", "remediation"):
                if data.get(f) is None:
                    data[f] = ""
            if "type" in data and "risk_type" not in data:
                data["risk_type"] = data.pop("type")
            if "issue" in data and "description" not in data:
                data["description"] = data.pop("issue")
            if "fix" in data and "remediation" not in data:
                data["remediation"] = data.pop("fix")
            if "recommendation" in data and "remediation" not in data:
                data["remediation"] = data.pop("recommendation")
            sev = data.get("severity", "medium")
            if sev not in ("high", "medium", "low"):
                data["severity"] = "medium"
        return data


class ATSReport(BaseModel):
    """Complete ATS compatibility report."""

    risks: list[ATSRisk] = []
    overall_ats_score: int = Field(default=50, ge=0, le=100)
    critical_issues_count: int = 0
    format_recommendation: str = "docx"
    summary: str = ""

    @model_validator(mode="before")
    @classmethod
    def normalize(cls, data):
        if not isinstance(data, dict):
            return data
        if "issues" in data and "risks" not in data:
            data["risks"] = data.pop("issues")
        if "score" in data and "overall_ats_score" not in data:
            data["overall_ats_score"] = data.pop("score")
        if "ats_score" in data and "overall_ats_score" not in data:
            data["overall_ats_score"] = data.pop("ats_score")
        if "recommendation" in data and "format_recommendation" not in data:
            data["format_recommendation"] = data.pop("recommendation")
        if data.get("format_recommendation") is None:
            data["format_recommendation"] = "docx"
        if data.get("summary") is None:
            data["summary"] = ""
        val = data.get("risks")
        if isinstance(val, dict):
            data["risks"] = list(val.values())
        if "overall_ats_score" in data:
            try:
                data["overall_ats_score"] = max(0, min(100, int(data["overall_ats_score"])))
            except (ValueError, TypeError):
                data["overall_ats_score"] = 50
        if "critical_issues_count" not in data:
            risks = data.get("risks", [])
            if isinstance(risks, list):
                data["critical_issues_count"] = sum(
                    1 for r in risks
                    if isinstance(r, dict) and r.get("severity") == "high"
                )
        return data


class ATSCheckInput(BaseModel):
    """Input schema for the ATS check agent."""

    raw_text: str
    file_format: str  # "pdf", "docx", "txt"
    format_indicators: str  # JSON string of format-specific indicators


class ATSCheckAgent(BaseAgent[ATSCheckInput, ATSReport]):
    """Analyzes resume for ATS compatibility risks.

    Checks for formatting issues (tables, columns, images), structural
    problems (non-standard headers, missing sections), and encoding
    concerns that could cause ATS parsing failures.
    """

    agent_name = "ats_check"
    max_output_tokens = 1500
    temperature = 0.1

    def __init__(
        self,
        llm_service: LLMService,
        prompt_loader: PromptLoader,
    ) -> None:
        super().__init__(llm_service=llm_service, prompt_loader=prompt_loader)

    async def execute(self, input_data: ATSCheckInput) -> ATSReport:
        """Analyze a resume for ATS compatibility issues.

        Args:
            input_data: Raw resume text, file format, and format-specific indicators.

        Returns:
            ATSReport with identified risks, scores, and remediation suggestions.
        """
        templates = self._load_prompt_template()
        system_prompt = templates["system_prompt"]

        user_template = Template(templates["user_prompt_template"])
        user_prompt = user_template.safe_substitute(
            raw_text=input_data.raw_text,
            file_format=input_data.file_format,
            format_indicators=input_data.format_indicators,
        )

        response_schema = ATSReport.model_json_schema()

        response = await self._call_llm(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            response_schema=response_schema,
        )

        report = ATSReport.model_validate(response.content)

        # Validate critical_issues_count
        actual_critical = sum(1 for r in report.risks if r.severity == "high")
        if report.critical_issues_count != actual_critical:
            logger.info(
                "Correcting critical_issues_count from %d to %d",
                report.critical_issues_count,
                actual_critical,
            )
            report.critical_issues_count = actual_critical

        is_valid = await self.validate_output(report)
        if not is_valid:
            logger.warning("ATS check output failed validation, returning as-is")

        return report
