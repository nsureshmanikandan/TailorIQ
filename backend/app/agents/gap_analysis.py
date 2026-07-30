"""Gap analysis agent — identifies gaps between resume and JD requirements.

Analyzes parsed resume against parsed JD and scoring output to produce
a detailed report of missing skills, certifications, and experience.
"""

import json
import logging
from string import Template

from pydantic import BaseModel

from app.agents.base import BaseAgent
from app.schemas.jd_parsed import ParsedJD
from app.schemas.resume_parsed import ParsedResume
from app.schemas.scoring import GapReport, ScoreOutput
from app.services.llm_service import LLMService
from app.services.prompt_loader import PromptLoader

logger = logging.getLogger(__name__)


class GapAnalysisInput(BaseModel):
    """Input schema for the gap analysis agent."""

    parsed_resume: ParsedResume
    parsed_jd: ParsedJD
    score_output: ScoreOutput


class GapAnalysisAgent(BaseAgent[GapAnalysisInput, GapReport]):
    """Identifies and classifies gaps between a resume and job requirements.

    Produces a structured GapReport with severity classification,
    transferability assessment, and actionable suggestions.
    Does NOT penalize career gaps, job-hopping, or non-traditional experience.
    """

    agent_name = "gap_analysis"
    max_output_tokens = 3000
    temperature = 0.3

    def __init__(
        self,
        llm_service: LLMService,
        prompt_loader: PromptLoader,
    ) -> None:
        super().__init__(llm_service=llm_service, prompt_loader=prompt_loader)

    async def execute(self, input_data: GapAnalysisInput) -> GapReport:
        """Analyze gaps between resume and JD requirements.

        Args:
            input_data: Parsed resume, parsed JD, and initial scoring output.

        Returns:
            GapReport with classified gaps and recommendations.
        """
        templates = self._load_prompt_template()
        system_prompt = templates["system_prompt"]

        resume_json = input_data.parsed_resume.model_dump_json(indent=2)
        jd_json = input_data.parsed_jd.model_dump_json(indent=2)
        scores_json = input_data.score_output.model_dump_json(indent=2)

        user_template = Template(templates["user_prompt_template"])
        user_prompt = user_template.safe_substitute(
            resume_json=resume_json,
            jd_json=jd_json,
            scores_json=scores_json,
        )

        response_schema = GapReport.model_json_schema()

        response = await self._call_llm(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            response_schema=response_schema,
        )

        gap_report = GapReport.model_validate(response.content)

        # Validate counts match gaps list
        gap_report = self._validate_counts(gap_report)

        is_valid = await self.validate_output(gap_report)
        if not is_valid:
            logger.warning("Gap analysis output failed validation, returning as-is")

        return gap_report

    def _validate_counts(self, report: GapReport) -> GapReport:
        """Ensure critical_count and recommended_count match the gaps list."""
        critical = sum(1 for g in report.gaps if g.severity == "critical")
        recommended = sum(1 for g in report.gaps if g.severity == "recommended")

        if report.critical_count != critical:
            logger.info("Correcting critical_count from %d to %d", report.critical_count, critical)
            report.critical_count = critical

        if report.recommended_count != recommended:
            logger.info("Correcting recommended_count from %d to %d", report.recommended_count, recommended)
            report.recommended_count = recommended

        return report
