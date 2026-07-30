"""Prompt template loader for versioned YAML-based agent prompts.

Loads system and user prompt templates from the prompts directory structure:
    backend/app/prompts/{version}/{agent_name}.yaml

Each YAML file is expected to contain:
    system_prompt: str
    user_prompt_template: str (with {variable} placeholders)
"""

import logging
from functools import lru_cache
from pathlib import Path
from string import Template
from typing import Any

import yaml

logger = logging.getLogger(__name__)

# Base path for prompt templates relative to the app package
_PROMPTS_BASE_DIR = Path(__file__).parent.parent / "prompts"


class PromptLoadError(Exception):
    """Raised when a prompt template cannot be loaded or parsed."""


class PromptLoader:
    """Loads and caches versioned YAML prompt templates for agents.

    Supports variable substitution in user_prompt_template using Python's
    string.Template syntax (e.g., ${variable_name}).
    """

    def __init__(self, prompts_dir: Path | None = None) -> None:
        """Initialize the prompt loader.

        Args:
            prompts_dir: Base directory for prompt templates.
                Defaults to backend/app/prompts/.
        """
        self._prompts_dir = prompts_dir or _PROMPTS_BASE_DIR

    def load(self, agent_name: str, version: str = "v1") -> dict[str, str]:
        """Load a prompt template for the given agent and version.

        Args:
            agent_name: The agent's name (matches the YAML filename without extension).
            version: The prompt version directory (e.g., "v1").

        Returns:
            Dictionary with 'system_prompt' and 'user_prompt_template' keys.

        Raises:
            PromptLoadError: If the file cannot be found or parsed.
        """
        return self._load_cached(agent_name, version)

    @lru_cache(maxsize=64)
    def _load_cached(self, agent_name: str, version: str) -> dict[str, str]:
        """Cache-backed prompt template loading.

        Args:
            agent_name: The agent's name.
            version: The prompt version directory.

        Returns:
            Dictionary with system_prompt and user_prompt_template.
        """
        file_path = self._prompts_dir / version / f"{agent_name}.yaml"

        if not file_path.exists():
            raise PromptLoadError(
                f"Prompt template not found: {file_path}. "
                f"Ensure prompts/{version}/{agent_name}.yaml exists."
            )

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise PromptLoadError(
                f"Failed to parse YAML prompt template at {file_path}: {e}"
            ) from e

        if not isinstance(data, dict):
            raise PromptLoadError(
                f"Prompt template at {file_path} must be a YAML mapping, "
                f"got {type(data).__name__}."
            )

        system_prompt = data.get("system_prompt")
        user_prompt_template = data.get("user_prompt_template")

        if not system_prompt:
            raise PromptLoadError(
                f"Prompt template at {file_path} is missing 'system_prompt' key."
            )
        if not user_prompt_template:
            raise PromptLoadError(
                f"Prompt template at {file_path} is missing 'user_prompt_template' key."
            )

        return {
            "system_prompt": str(system_prompt),
            "user_prompt_template": str(user_prompt_template),
        }

    def render_user_prompt(
        self,
        agent_name: str,
        version: str = "v1",
        **variables: Any,
    ) -> str:
        """Load and render the user prompt template with variable substitution.

        Uses safe_substitute so missing variables produce no errors.

        Args:
            agent_name: The agent's name.
            version: The prompt version directory.
            **variables: Key-value pairs for template variable substitution.

        Returns:
            Rendered user prompt string with variables substituted.
        """
        templates = self.load(agent_name=agent_name, version=version)
        template = Template(templates["user_prompt_template"])
        return template.safe_substitute(**variables)

    def clear_cache(self) -> None:
        """Clear the prompt template cache (useful for testing or hot-reload)."""
        self._load_cached.cache_clear()
