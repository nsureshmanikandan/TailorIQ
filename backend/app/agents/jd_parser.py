"""Job description parser agent — extracts structured requirements from JD text.

Calls the LLM with structured output to parse job descriptions into
the ParsedJD model, distinguishing must-have from nice-to-have requirements.
"""

import logging
from string import Template

from pydantic import BaseModel

from app.agents.base import BaseAgent
from app.schemas.jd_parsed import ParsedJD
from app.services.llm_service import LLMService
from app.services.prompt_loader import PromptLoader

logger = logging.getLogger(__name__)


class JDParserInput(BaseModel):
    """Input schema for the JD parser agent."""

    raw_text: str


class JDParserAgent(BaseAgent[JDParserInput, ParsedJD]):
    """Parses raw job description text into structured ParsedJD data.

    Extracts role requirements, skills (must-have vs nice-to-have),
    responsibilities, certifications, and ATS keywords.
    """

    agent_name = "jd_parser"
    max_output_tokens = 3000
    temperature = 0.1

    def __init__(
        self,
        llm_service: LLMService,
        prompt_loader: PromptLoader,
    ) -> None:
        super().__init__(llm_service=llm_service, prompt_loader=prompt_loader)

    async def execute(self, input_data: JDParserInput) -> ParsedJD:
        """Parse raw job description text into structured data.

        Args:
            input_data: Raw text of the job description.

        Returns:
            ParsedJD with extracted structured requirements.
        """
        templates = self._load_prompt_template()
        system_prompt = templates["system_prompt"]

        user_template = Template(templates["user_prompt_template"])
        user_prompt = user_template.safe_substitute(
            raw_text=input_data.raw_text,
        )

        response_schema = ParsedJD.model_json_schema()

        response = await self._call_llm(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            response_schema=response_schema,
        )

        parsed_jd = ParsedJD.model_validate(response.content)

        is_valid = await self.validate_output(parsed_jd)
        if not is_valid:
            logger.warning("JD parser output failed validation, returning as-is")

        return parsed_jd
