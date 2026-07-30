"""Base agent abstract class for all AI agents in the pipeline.

Provides structured output enforcement, token tracking, OpenTelemetry span
creation, and prompt template loading. All concrete agents inherit from this
class and implement the `execute` method.
"""

import json
import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Generic, TypeVar

from opentelemetry import trace
from pydantic import BaseModel

from app.services.llm_service import LLMResponse, LLMService
from app.services.prompt_loader import PromptLoader

logger = logging.getLogger(__name__)

TInput = TypeVar("TInput", bound=BaseModel)
TOutput = TypeVar("TOutput", bound=BaseModel)

tracer = trace.get_tracer("resumejdmatch.agents")


class BaseAgent(ABC, Generic[TInput, TOutput]):
    """Abstract base class for all AI agents.

    Attributes:
        agent_name: Unique identifier for this agent (used in telemetry and prompts).
        max_output_tokens: Maximum output tokens allowed for this agent's LLM calls.
        temperature: LLM temperature for controlling response creativity.
        prompt_version: Version of the prompt template directory to load from.
    """

    agent_name: str
    max_output_tokens: int
    temperature: float = 0.2
    prompt_version: str = "v1"

    def __init__(
        self,
        llm_service: LLMService,
        prompt_loader: PromptLoader,
    ) -> None:
        """Initialize the base agent.

        Args:
            llm_service: The LLM service client for making API calls.
            prompt_loader: The prompt template loader for reading YAML prompts.
        """
        from app.config import get_settings

        self._llm_service = llm_service
        self._prompt_loader = prompt_loader
        self._total_input_tokens: int = 0
        self._total_output_tokens: int = 0

        # Allow .env / config to override the class-level max_output_tokens.
        # Convention: LLM_MAX_TOKENS_<AGENT_NAME_UPPER> e.g. LLM_MAX_TOKENS_RESUME_PARSER
        settings = get_settings()
        key = f"LLM_MAX_TOKENS_{self.agent_name.upper()}"
        override = getattr(settings, key, None)
        if override is not None:
            self.max_output_tokens = override

    @abstractmethod
    async def execute(self, input_data: TInput) -> TOutput:
        """Execute the agent's primary task.

        Args:
            input_data: Validated input conforming to the agent's input schema.

        Returns:
            Structured output conforming to the agent's output schema.
        """
        ...

    async def validate_output(self, output: TOutput) -> bool:
        """Validate output against the agent's expected schema.

        Default implementation checks that the output is a valid Pydantic model.
        Subclasses may override for agent-specific validation rules.

        Args:
            output: The output to validate.

        Returns:
            True if valid, False otherwise.
        """
        try:
            if isinstance(output, BaseModel):
                output.model_validate(output.model_dump())
                return True
            return False
        except Exception as e:
            logger.warning(
                "Output validation failed for agent %s: %s",
                self.agent_name,
                str(e),
            )
            return False

    async def health_check(self) -> bool:
        """Check if the agent is operational by verifying LLM connectivity.

        Returns:
            True if the agent can reach the LLM service.
        """
        try:
            return await self._llm_service.health_check()
        except Exception as e:
            logger.error(
                "Health check failed for agent %s: %s",
                self.agent_name,
                str(e),
            )
            return False

    async def _call_llm(
        self,
        system_prompt: str,
        user_prompt: str,
        response_schema: dict | None = None,
    ) -> LLMResponse:
        """Call the LLM service with tracing and token tracking.

        Creates an OpenTelemetry span for the call, tracks token usage,
        and enforces the agent's max_output_tokens constraint.

        Args:
            system_prompt: The system prompt to send.
            user_prompt: The user prompt to send.
            response_schema: Optional JSON schema for structured output enforcement.

        Returns:
            LLMResponse containing parsed content and token usage metadata.
        """
        with tracer.start_as_current_span(
            f"{self.agent_name}.llm_call",
            attributes={
                "agent.name": self.agent_name,
                "agent.prompt_version": self.prompt_version,
                "agent.temperature": self.temperature,
                "agent.max_output_tokens": self.max_output_tokens,
            },
        ) as span:
            response = await self._llm_service.chat_completion(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                max_output_tokens=self.max_output_tokens,
                temperature=self.temperature,
                response_schema=response_schema,
            )

            # Track token usage
            self._total_input_tokens += response.input_tokens
            self._total_output_tokens += response.output_tokens

            # Attach token metrics to the span
            span.set_attribute("llm.input_tokens", response.input_tokens)
            span.set_attribute("llm.output_tokens", response.output_tokens)
            span.set_attribute("llm.model", response.model)

            logger.info(
                "Agent %s LLM call: input_tokens=%d, output_tokens=%d, model=%s",
                self.agent_name,
                response.input_tokens,
                response.output_tokens,
                response.model,
            )

            return response

    def _load_prompt_template(self) -> dict[str, str]:
        """Load the prompt template for this agent from YAML.

        Looks up the template by agent_name and prompt_version from the
        configured prompts directory.

        Returns:
            Dictionary with 'system_prompt' and 'user_prompt_template' keys.
        """
        return self._prompt_loader.load(
            agent_name=self.agent_name,
            version=self.prompt_version,
        )

    @property
    def total_input_tokens(self) -> int:
        """Total input tokens consumed across all calls by this agent."""
        return self._total_input_tokens

    @property
    def total_output_tokens(self) -> int:
        """Total output tokens consumed across all calls by this agent."""
        return self._total_output_tokens

    def reset_token_counters(self) -> None:
        """Reset token usage counters to zero."""
        self._total_input_tokens = 0
        self._total_output_tokens = 0
