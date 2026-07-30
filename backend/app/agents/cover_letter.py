"""Cover letter generation agent — creates targeted cover letters.

Generates concise, compelling cover letters grounded in resume evidence
and aligned with specific JD requirements.
"""

import json
import logging
from string import Template

from pydantic import BaseModel

from app.agents.base import BaseAgent
from app.schemas.cover_letter import CoverLetter
from app.schemas.jd_parsed import ParsedJD
from app.schemas.resume_parsed import ParsedResume
from app.schemas.tailored import TailoredResume
from app.services.llm_service import LLMService
from app.services.prompt_loader import PromptLoader

logger = logging.getLogger(__name__)


class CoverLetterInput(BaseModel):
    """Input schema for the cover letter agent."""

    parsed_resume: ParsedResume
    parsed_jd: ParsedJD
    tailored_resume: TailoredResume


class CoverLetterAgent(BaseAgent[CoverLetterInput, CoverLetter]):
    """Generates a cover letter (250-350 words) grounded in resume evidence.

    References 1-2 specific JD requirements and cites actual resume
    achievements as evidence. Never fabricates claims.
    """

    agent_name = "cover_letter"
    max_output_tokens = 1500
    temperature = 0.6

    def __init__(
        self,
        llm_service: LLMService,
        prompt_loader: PromptLoader,
    ) -> None:
        super().__init__(llm_service=llm_service, prompt_loader=prompt_loader)

    async def execute(self, input_data: CoverLetterInput) -> CoverLetter:
        """Generate a cover letter for the target role.

        Args:
            input_data: Parsed resume, parsed JD, and tailored resume.

        Returns:
            CoverLetter with content and grounding metadata.
        """
        templates = self._load_prompt_template()
        system_prompt = templates["system_prompt"]

        resume_json = input_data.parsed_resume.model_dump_json(indent=2)
        jd_json = input_data.parsed_jd.model_dump_json(indent=2)
        tailored_json = input_data.tailored_resume.model_dump_json(indent=2)

        user_template = Template(templates["user_prompt_template"])
        user_prompt = user_template.safe_substitute(
            resume_json=resume_json,
            jd_json=jd_json,
            tailored_json=tailored_json,
        )

        response_schema = CoverLetter.model_json_schema()

        response = await self._call_llm(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            response_schema=response_schema,
        )

        cover_letter = CoverLetter.model_validate(response.content)

        # Validate word count matches actual content
        actual_word_count = len(cover_letter.content.split())
        clamped = min(actual_word_count, 1000)
        if abs(cover_letter.word_count - actual_word_count) > 5:
            logger.info(
                "Correcting word_count from %d to %d",
                cover_letter.word_count,
                actual_word_count,
            )
            cover_letter.word_count = clamped

        is_valid = await self.validate_output(cover_letter)
        if not is_valid:
            logger.warning("Cover letter output failed validation, returning as-is")

        return cover_letter
