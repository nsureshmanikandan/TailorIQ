"""Resume tailoring agent — optimizes resume content for a target JD.

Rewrites and restructures resume content to better align with the job description
while preserving all factual claims from the original resume.
"""

import json
import logging
from string import Template

from pydantic import BaseModel

from app.agents.base import BaseAgent
from app.schemas.jd_parsed import ParsedJD
from app.schemas.resume_parsed import ParsedResume
from app.schemas.scoring import GapReport
from app.schemas.tailored import TailoredResume
from app.services.llm_service import LLMService
from app.services.prompt_loader import PromptLoader

logger = logging.getLogger(__name__)


class ResumeTailoringInput(BaseModel):
    """Input schema for the resume tailoring agent."""

    parsed_resume: ParsedResume
    parsed_jd: ParsedJD
    gap_report: GapReport
    source_text: str  # Original resume text for fact-checking


class ResumeTailoringAgent(BaseAgent[ResumeTailoringInput, TailoredResume]):
    """Tailors a resume to align with a target job description.

    CRITICAL: Preserves all factual claims from the original resume.
    Adds relevant keywords, restructures content for better alignment,
    and maintains ATS-safe formatting throughout.
    """

    agent_name = "resume_tailoring"
    max_output_tokens = 6000
    temperature = 0.4

    def __init__(
        self,
        llm_service: LLMService,
        prompt_loader: PromptLoader,
    ) -> None:
        super().__init__(llm_service=llm_service, prompt_loader=prompt_loader)

    async def execute(self, input_data: ResumeTailoringInput) -> TailoredResume:
        """Tailor a resume for a specific job description.

        Args:
            input_data: Parsed resume, parsed JD, gap report, and original text.

        Returns:
            TailoredResume with optimized content and change tracking.
        """
        templates = self._load_prompt_template()
        system_prompt = templates["system_prompt"]

        resume_json = input_data.parsed_resume.model_dump_json(indent=2)
        jd_json = input_data.parsed_jd.model_dump_json(indent=2)
        gap_json = input_data.gap_report.model_dump_json(indent=2)

        user_template = Template(templates["user_prompt_template"])
        user_prompt = user_template.safe_substitute(
            resume_json=resume_json,
            jd_json=jd_json,
            gap_json=gap_json,
            source_text=input_data.source_text,
        )

        response_schema = TailoredResume.model_json_schema()

        response = await self._call_llm(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            response_schema=response_schema,
        )

        tailored_resume = TailoredResume.model_validate(response.content)

        is_valid = await self.validate_output(tailored_resume)
        if not is_valid:
            logger.warning("Resume tailoring output failed validation, returning as-is")

        return tailored_resume
