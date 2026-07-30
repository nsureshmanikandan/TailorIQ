"""Resume parser agent — extracts structured data from raw resume text.

Calls the LLM with a structured output schema to parse resumes into
the ParsedResume model, handling multiple file formats.
"""

import json
import logging
from string import Template

from pydantic import BaseModel

from app.agents.base import BaseAgent
from app.schemas.resume_parsed import ParsedResume
from app.services.llm_service import LLMService
from app.services.prompt_loader import PromptLoader

logger = logging.getLogger(__name__)


class ResumeParserInput(BaseModel):
    """Input schema for the resume parser agent."""

    raw_text: str
    file_format: str  # "pdf", "docx", "txt"


class ResumeParserAgent(BaseAgent[ResumeParserInput, ParsedResume]):
    """Parses raw resume text into structured ParsedResume data.

    Uses LLM with structured output enforcement to extract skills,
    experience, education, certifications, and metadata from resumes.
    """

    agent_name = "resume_parser"
    max_output_tokens = 4000
    temperature = 0.1

    def __init__(
        self,
        llm_service: LLMService,
        prompt_loader: PromptLoader,
    ) -> None:
        super().__init__(llm_service=llm_service, prompt_loader=prompt_loader)

    async def execute(self, input_data: ResumeParserInput) -> ParsedResume:
        """Parse raw resume text into structured data.

        Args:
            input_data: Raw text and file format of the resume.

        Returns:
            ParsedResume with extracted structured data.
        """
        # Load prompt template
        templates = self._load_prompt_template()
        system_prompt = templates["system_prompt"]

        # Render user prompt with input variables
        user_template = Template(templates["user_prompt_template"])
        user_prompt = user_template.safe_substitute(
            raw_text=input_data.raw_text,
            file_format=input_data.file_format,
        )

        # Get JSON schema for structured output
        response_schema = ParsedResume.model_json_schema()

        # Call LLM with structured output enforcement
        response = await self._call_llm(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            response_schema=response_schema,
        )

        # Validate and return parsed resume
        parsed_resume = ParsedResume.model_validate(response.content)

        # Validate output
        is_valid = await self.validate_output(parsed_resume)
        if not is_valid:
            logger.warning("Resume parser output failed validation, returning as-is")

        return parsed_resume
