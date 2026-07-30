"""Azure OpenAI LLM service wrapper.

Provides a structured interface for making Azure OpenAI API calls with:
- Structured output enforcement via JSON schema response_format
- Token usage tracking (input and output)
- Per-agent max_output_tokens enforcement
- Configurable temperature and seed for reproducibility
- Parsed JSON response with metadata
"""

import json
import logging
from dataclasses import dataclass
from typing import Any

from openai import AsyncAzureOpenAI
from openai.types.chat import ChatCompletion

from app.config import Settings, get_settings

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class LLMResponse:
    """Response from an LLM call with parsed content and usage metadata.

    Attributes:
        content: Parsed JSON content from the LLM response.
        raw_content: Raw string content from the response.
        input_tokens: Number of prompt (input) tokens used.
        output_tokens: Number of completion (output) tokens used.
        model: The model deployment that served the request.
    """

    content: dict[str, Any]
    raw_content: str
    input_tokens: int
    output_tokens: int
    model: str


class LLMService:
    """Azure OpenAI client wrapper for structured LLM interactions.

    Handles authentication, request formatting, structured output enforcement,
    and token usage reporting for all agent LLM calls.
    """

    def __init__(self, settings: Settings | None = None) -> None:
        """Initialize the LLM service with Azure OpenAI configuration.

        Args:
            settings: Application settings. If None, loads from environment.
        """
        self._settings = settings or get_settings()
        self._client = AsyncAzureOpenAI(
            azure_endpoint=self._settings.AZURE_OPENAI_ENDPOINT,
            api_key=self._settings.AZURE_OPENAI_API_KEY.get_secret_value(),
            api_version=self._settings.AZURE_OPENAI_API_VERSION,
        )
        self._deployment = self._settings.AZURE_OPENAI_DEPLOYMENT_NAME
        self._fallback_deployment = self._settings.AZURE_OPENAI_FALLBACK_DEPLOYMENT

    async def chat_completion(
        self,
        system_prompt: str,
        user_prompt: str,
        max_output_tokens: int = 4096,
        temperature: float = 0.2,
        response_schema: dict[str, Any] | None = None,
        seed: int | None = 42,
        deployment_override: str | None = None,
    ) -> LLMResponse:
        """Make a chat completion request to Azure OpenAI.

        Args:
            system_prompt: System message setting agent behavior.
            user_prompt: User message with the task content.
            max_output_tokens: Maximum tokens for the completion response.
            temperature: Sampling temperature (0.0 - 2.0).
            response_schema: Optional JSON schema for structured output enforcement.
                When provided, uses Azure OpenAI's response_format=json_schema.
            seed: Random seed for reproducibility. Defaults to 42.
            deployment_override: Optional deployment name to use instead of default.

        Returns:
            LLMResponse with parsed content and token usage metadata.

        Raises:
            openai.RateLimitError: When rate limited by Azure OpenAI.
            openai.APITimeoutError: When the request times out.
            openai.APIError: For other API errors.
            json.JSONDecodeError: When response cannot be parsed as JSON.
        """
        deployment = deployment_override or self._deployment

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        kwargs: dict[str, Any] = {
            "model": deployment,
            "messages": messages,
        }

        # GPT-5 mini (reasoning model) does not support max_tokens,
        # max_completion_tokens, temperature, or seed in some SDK versions.
        # Omit all of these for compatibility.

        if seed is not None:
            pass  # Reasoning models don't support seed

        if response_schema is not None:
            # Use simple json_object mode - strict json_schema mode
            # may not be supported by all models/API versions
            kwargs["response_format"] = {"type": "json_object"}
        else:
            # Request JSON output even without a strict schema
            kwargs["response_format"] = {"type": "json_object"}

        completion: ChatCompletion = await self._client.chat.completions.create(
            **kwargs
        )

        # Extract response content
        choice = completion.choices[0]
        raw_content = choice.message.content or ""

        # Parse JSON content
        try:
            content = json.loads(raw_content)
        except json.JSONDecodeError:
            logger.error(
                "Failed to parse LLM response as JSON for deployment %s: %s",
                deployment,
                raw_content[:500],
            )
            raise

        logger.info(
            "LLM response content (first 400 chars): %s",
            raw_content[:400],
        )

        # Unwrap single-key responses — LLM sometimes nests the entire output
        # under one parent key, e.g. {"tailored_resume": {...}} instead of {...}
        if isinstance(content, dict) and len(content) == 1:
            single_key = next(iter(content))
            single_val = content[single_key]
            if isinstance(single_val, dict):
                logger.info("Unwrapping single-key LLM response (key=%s)", single_key)
                content = single_val

        # Extract token usage
        usage = completion.usage
        input_tokens = usage.prompt_tokens if usage else 0
        output_tokens = usage.completion_tokens if usage else 0

        logger.debug(
            "LLM call completed: deployment=%s, input_tokens=%d, output_tokens=%d",
            deployment,
            input_tokens,
            output_tokens,
        )

        return LLMResponse(
            content=content,
            raw_content=raw_content,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            model=completion.model or deployment,
        )

    async def health_check(self) -> bool:
        """Verify connectivity to Azure OpenAI."""
        try:
            await self._client.chat.completions.create(
                model=self._deployment,
                messages=[{"role": "user", "content": "ping"}],
            )
            return True
        except Exception as e:
            logger.warning("LLM health check failed: %s", str(e))
            return False

    @property
    def deployment_name(self) -> str:
        """Current primary deployment name."""
        return self._deployment

    @property
    def fallback_deployment_name(self) -> str:
        """Fallback deployment name for circuit breaker scenarios."""
        return self._fallback_deployment
