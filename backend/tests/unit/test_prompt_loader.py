"""Unit tests for the prompt loader module."""

import tempfile
from pathlib import Path

import pytest
import yaml

from app.services.prompt_loader import PromptLoadError, PromptLoader


@pytest.fixture
def temp_prompts_dir(tmp_path):
    """Create a temporary prompts directory with a test template."""
    v1_dir = tmp_path / "v1"
    v1_dir.mkdir()

    template = {
        "system_prompt": "You are a resume parser. Extract structured data.",
        "user_prompt_template": "Parse this resume:\n${resume_text}\n\nFormat: ${format}",
    }

    with open(v1_dir / "resume_parser.yaml", "w") as f:
        yaml.dump(template, f)

    return tmp_path


@pytest.fixture
def loader(temp_prompts_dir):
    """Create a PromptLoader with the temp directory."""
    return PromptLoader(prompts_dir=temp_prompts_dir)


class TestPromptLoader:
    """Tests for PromptLoader."""

    def test_load_existing_template(self, loader: PromptLoader):
        """Loads a valid template file correctly."""
        result = loader.load("resume_parser", version="v1")
        assert "system_prompt" in result
        assert "user_prompt_template" in result
        assert "resume parser" in result["system_prompt"].lower()

    def test_load_nonexistent_agent(self, loader: PromptLoader):
        """Raises error for missing agent template."""
        with pytest.raises(PromptLoadError):
            loader.load("nonexistent_agent", version="v1")

    def test_load_nonexistent_version(self, loader: PromptLoader):
        """Raises error for missing version directory."""
        with pytest.raises(PromptLoadError):
            loader.load("resume_parser", version="v99")

    def test_render_user_prompt(self, loader: PromptLoader):
        """Renders template with variable substitution."""
        rendered = loader.render_user_prompt(
            "resume_parser",
            version="v1",
            resume_text="John Doe, Python Developer",
            format="JSON",
        )
        assert "John Doe, Python Developer" in rendered
        assert "JSON" in rendered

    def test_render_missing_variable_safe(self, loader: PromptLoader):
        """Missing variables are left as placeholders (safe_substitute)."""
        rendered = loader.render_user_prompt(
            "resume_parser",
            version="v1",
            resume_text="Some text",
            # 'format' variable not provided
        )
        assert "Some text" in rendered
        # safe_substitute leaves ${format} as-is
        assert "${format}" in rendered

    def test_invalid_yaml_raises(self, tmp_path):
        """Invalid YAML content raises PromptLoadError."""
        v1_dir = tmp_path / "v1"
        v1_dir.mkdir()

        with open(v1_dir / "bad_agent.yaml", "w") as f:
            f.write("{{invalid yaml content::")

        loader = PromptLoader(prompts_dir=tmp_path)
        with pytest.raises(PromptLoadError):
            loader.load("bad_agent", version="v1")

    def test_missing_system_prompt_raises(self, tmp_path):
        """YAML without system_prompt key raises PromptLoadError."""
        v1_dir = tmp_path / "v1"
        v1_dir.mkdir()

        template = {"user_prompt_template": "just a user prompt"}

        with open(v1_dir / "incomplete.yaml", "w") as f:
            yaml.dump(template, f)

        loader = PromptLoader(prompts_dir=tmp_path)
        with pytest.raises(PromptLoadError):
            loader.load("incomplete", version="v1")

    def test_cache_clearing(self, loader: PromptLoader):
        """Cache can be cleared without errors."""
        loader.load("resume_parser", version="v1")
        loader.clear_cache()
        # Should still work after clearing
        result = loader.load("resume_parser", version="v1")
        assert "system_prompt" in result
