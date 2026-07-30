"""Interview preparation agent — generates targeted interview questions.

Creates 11-14 interview questions (behavioral + technical) with STAR
method preparation guidance based on resume evidence and JD requirements.
"""

import json
import logging
from string import Template

from pydantic import BaseModel

from app.agents.base import BaseAgent
from app.schemas.interview import InterviewGuide
from app.schemas.jd_parsed import ParsedJD
from app.schemas.resume_parsed import ParsedResume
from app.schemas.scoring import GapReport
from app.services.llm_service import LLMService
from app.services.prompt_loader import PromptLoader

logger = logging.getLogger(__name__)


class InterviewPrepInput(BaseModel):
    """Input schema for the interview prep agent."""

    parsed_resume: ParsedResume
    parsed_jd: ParsedJD
    gap_report: GapReport


class InterviewPrepAgent(BaseAgent[InterviewPrepInput, InterviewGuide]):
    """Generates an interview preparation guide with 11-14 questions.

    Produces 8-10 behavioral questions (STAR method) and 3-4 technical
    questions based on JD requirements, identified gaps, and resume evidence.
    """

    agent_name = "interview_prep"
    max_output_tokens = 6000
    temperature = 0.5

    def __init__(
        self,
        llm_service: LLMService,
        prompt_loader: PromptLoader,
    ) -> None:
        super().__init__(llm_service=llm_service, prompt_loader=prompt_loader)

    async def execute(self, input_data: InterviewPrepInput) -> InterviewGuide:
        """Generate interview preparation questions and guidance.

        Args:
            input_data: Parsed resume, parsed JD, and gap report.

        Returns:
            InterviewGuide with behavioral and technical questions.
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
        )

        response_schema = InterviewGuide.model_json_schema()

        response = await self._call_llm(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            response_schema=response_schema,
        )

        try:
            guide = InterviewGuide.model_validate(response.content)
        except Exception as e:
            logger.error(
                "InterviewGuide validation failed: %s\nRaw response (first 800 chars): %s",
                str(e),
                response.raw_content[:800],
            )
            raise

        # Validate total_count matches actual question count
        actual_count = len(guide.behavioral_questions) + len(guide.technical_questions)
        if guide.total_count != actual_count:
            logger.info(
                "Correcting total_count from %d to %d",
                guide.total_count,
                actual_count,
            )
            guide.total_count = actual_count

        is_valid = await self.validate_output(guide)
        if not is_valid:
            logger.warning("Interview prep output failed validation, returning as-is")

        return guide
