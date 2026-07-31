"""Unit tests for LLMService dual-endpoint client selection."""

from unittest.mock import MagicMock, patch

from app.services.llm_service import LLMService


def _mock_settings(endpoint: str, deployment: str = "test-model") -> MagicMock:
    s = MagicMock()
    s.AZURE_OPENAI_ENDPOINT = endpoint
    s.AZURE_OPENAI_API_KEY.get_secret_value.return_value = "test-key"
    s.AZURE_OPENAI_DEPLOYMENT_NAME = deployment
    s.AZURE_OPENAI_FALLBACK_DEPLOYMENT = ""
    s.AZURE_OPENAI_API_VERSION = "2024-12-01-preview"
    return s


class TestLLMServiceClientSelection:
    """LLMService picks the right client based on endpoint URL."""

    def test_v1_endpoint_uses_async_openai(self):
        settings = _mock_settings(
            "https://resource.services.ai.azure.com/openai/v1"
        )
        with patch("app.services.llm_service.AsyncOpenAI") as mock_v1, \
             patch("app.services.llm_service.AsyncAzureOpenAI") as mock_azure:
            LLMService(settings=settings)
            mock_v1.assert_called_once_with(
                base_url="https://resource.services.ai.azure.com/openai/v1",
                api_key="test-key",
            )
            mock_azure.assert_not_called()

    def test_v1_endpoint_trailing_slash_normalised(self):
        """Trailing slash on v1 endpoint is stripped before comparison."""
        settings = _mock_settings(
            "https://resource.services.ai.azure.com/openai/v1/"
        )
        with patch("app.services.llm_service.AsyncOpenAI") as mock_v1, \
             patch("app.services.llm_service.AsyncAzureOpenAI"):
            LLMService(settings=settings)
            call_kwargs = mock_v1.call_args.kwargs
            assert call_kwargs["base_url"] == \
                "https://resource.services.ai.azure.com/openai/v1"

    def test_classic_endpoint_uses_async_azure_openai(self):
        settings = _mock_settings(
            "https://resource.services.ai.azure.com/"
        )
        with patch("app.services.llm_service.AsyncAzureOpenAI") as mock_azure, \
             patch("app.services.llm_service.AsyncOpenAI") as mock_v1:
            LLMService(settings=settings)
            mock_azure.assert_called_once_with(
                azure_endpoint="https://resource.services.ai.azure.com/",
                api_key="test-key",
                api_version="2024-12-01-preview",
            )
            mock_v1.assert_not_called()

    def test_classic_endpoint_no_trailing_slash(self):
        """Classic endpoint without trailing slash still uses AsyncAzureOpenAI."""
        settings = _mock_settings(
            "https://resource.services.ai.azure.com"
        )
        with patch("app.services.llm_service.AsyncAzureOpenAI") as mock_azure, \
             patch("app.services.llm_service.AsyncOpenAI") as mock_v1:
            LLMService(settings=settings)
            mock_azure.assert_called_once()
            mock_v1.assert_not_called()
