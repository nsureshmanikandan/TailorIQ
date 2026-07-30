"""Application configuration using Pydantic Settings.

All environment variables are loaded from .env files or the system environment.
Sensitive values (secrets, keys, passwords) use SecretStr to prevent accidental
logging or serialization of their plaintext values.
"""

from functools import lru_cache
from typing import Optional

from pydantic import SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    Settings are grouped by concern and use sensible defaults for local
    development where possible. Production deployments must set all
    required secrets via environment variables or a mounted .env file.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        # .env file takes priority over system environment variables
        env_file_override=True,
    )

    # ─── Database ────────────────────────────────────────────────────────────────
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/resumejdmatch"

    # ─── Azure OpenAI ────────────────────────────────────────────────────────────
    AZURE_OPENAI_ENDPOINT: str = ""
    AZURE_OPENAI_API_KEY: SecretStr = SecretStr("")
    AZURE_OPENAI_DEPLOYMENT_NAME: str = "gpt-4o-mini"
    AZURE_OPENAI_FALLBACK_DEPLOYMENT: str = ""
    AZURE_OPENAI_API_VERSION: str = "2024-08-01-preview"

    # ─── Azure Blob Storage ──────────────────────────────────────────────────────
    AZURE_STORAGE_CONNECTION_STRING: SecretStr = SecretStr("")
    AZURE_STORAGE_CONTAINER_NAME: str = "resumes"

    # ─── JWT Authentication ──────────────────────────────────────────────────────
    JWT_SECRET_KEY: SecretStr = SecretStr("CHANGE-ME-IN-PRODUCTION")
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ─── OAuth Providers ─────────────────────────────────────────────────────────
    OAUTH_GOOGLE_CLIENT_ID: str = ""
    OAUTH_GOOGLE_CLIENT_SECRET: SecretStr = SecretStr("")
    OAUTH_MICROSOFT_CLIENT_ID: str = ""
    OAUTH_MICROSOFT_CLIENT_SECRET: SecretStr = SecretStr("")

    # ─── OpenTelemetry ───────────────────────────────────────────────────────────
    OTEL_EXPORTER_OTLP_ENDPOINT: str = "http://localhost:4317"
    OTEL_SERVICE_NAME: str = "resumejdmatch-ai"

    # ─── Rate Limiting ───────────────────────────────────────────────────────────
    RATE_LIMIT_ANALYSES_PER_HOUR: int = 10
    REDIS_URL: str = "redis://localhost:6379/0"

    # ─── Email / SMTP ────────────────────────────────────────────────────────────
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: SecretStr = SecretStr("")
    FROM_EMAIL: str = "noreply@resumejdmatch.ai"

    # ─── Application ─────────────────────────────────────────────────────────────
    APP_ENV: str = "development"
    LOG_LEVEL: str = "INFO"
    CORS_ORIGINS: str = "http://localhost:5173"
    PROMPT_VERSION: str = "v1"
    SEMANTIC_MAPPINGS_PATH: str = "app/semantic/mappings.yaml"

    # ─── Agent Token Limits ──────────────────────────────────────────────────────
    # Defaults tuned for gpt-5.4-nano. When using a reasoning model (gpt-5-mini,
    # o-series), reasoning tokens count against these limits — increase by ~2x.
    LLM_MAX_TOKENS_RESUME_PARSER: int = 8000
    LLM_MAX_TOKENS_JD_PARSER: int = 3000
    LLM_MAX_TOKENS_MATCH_SCORING: int = 2000
    LLM_MAX_TOKENS_GAP_ANALYSIS: int = 3000
    LLM_MAX_TOKENS_ATS_CHECK: int = 1500
    LLM_MAX_TOKENS_RESUME_TAILORING: int = 10000
    LLM_MAX_TOKENS_CLAIM_VERIFICATION: int = 5000
    LLM_MAX_TOKENS_COVER_LETTER: int = 1500
    LLM_MAX_TOKENS_INTERVIEW_PREP: int = 6000

    @field_validator("LOG_LEVEL")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Ensure LOG_LEVEL is a valid Python logging level."""
        allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        upper = v.upper()
        if upper not in allowed:
            raise ValueError(f"LOG_LEVEL must be one of {allowed}, got '{v}'")
        return upper

    @field_validator("APP_ENV")
    @classmethod
    def validate_app_env(cls, v: str) -> str:
        """Ensure APP_ENV is a recognized environment name."""
        allowed = {"development", "staging", "production", "testing"}
        lower = v.lower()
        if lower not in allowed:
            raise ValueError(f"APP_ENV must be one of {allowed}, got '{v}'")
        return lower

    @property
    def cors_origin_list(self) -> list[str]:
        """Parse CORS_ORIGINS comma-separated string into a list."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    @property
    def is_production(self) -> bool:
        """Check if the application is running in production."""
        return self.APP_ENV == "production"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Cached settings singleton.

    Explicitly loads from .env file to ensure .env values take priority
    over any system environment variables that might conflict.
    """
    from pathlib import Path
    from dotenv import load_dotenv

    # Force .env to override system env vars
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        load_dotenv(env_path, override=True)

    return Settings()
