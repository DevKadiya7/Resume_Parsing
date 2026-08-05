"""Application configuration loaded from environment variables / .env file."""

import enum
from functools import lru_cache

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(str, enum.Enum):
    DEVELOPMENT = "development"
    TESTING = "testing"
    PRODUCTION = "production"


class Settings(BaseSettings):
    """Centralized application settings.

    All values can be overridden via environment variables or a `.env`
    file in the backend root. `ENVIRONMENT` selects which env file is
    loaded by default (see `.env.example` / `.env.test` / `.env.production`);
    an explicit `.env` (or real environment variables, which always win)
    still overrides it. See `.env.example` for the full variable list.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    ENVIRONMENT: Environment = Environment.DEVELOPMENT

    APP_NAME: str = "Resume Parsing Service"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False

    DATABASE_URL: str = "postgresql+asyncpg://resume_user:resume_password@localhost:5432/resume_db"

    UPLOAD_DIRECTORY: str = "uploads"
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10 MB — business-rule limit for a PDF upload
    MAX_REQUEST_SIZE: int = 12 * 1024 * 1024  # 12 MB — hard cap on any request body, enforced
    # by RequestSizeLimitMiddleware before routing; slightly above MAX_FILE_SIZE to leave
    # room for multipart overhead (boundaries, headers, form field names).

    # Comma-separated in the environment, e.g. "api.example.com,www.example.com".
    # "*" (the default) allows any Host header / origin — fine for local development,
    # but production deployments should set this explicitly (enforced below).
    ALLOWED_HOSTS: list[str] = ["*"]
    ALLOWED_ORIGINS: list[str] = ["*"]

    RATE_LIMIT_UPLOAD: str = "20/minute"
    RATE_LIMIT_PARSE: str = "20/minute"

    LOG_FORMAT: str = "text"  # "text" (human-readable console) or "json" (structured)

    @field_validator("ALLOWED_HOSTS", "ALLOWED_ORIGINS", mode="before")
    @classmethod
    def _split_comma_separated(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @model_validator(mode="after")
    def _validate_production_hardening(self) -> "Settings":
        """Fail fast at startup if production is misconfigured, instead of

        silently running with permissive settings that are fine for local
        development but unsafe as deployed.
        """
        if self.ENVIRONMENT == Environment.PRODUCTION:
            problems = []
            if self.DEBUG:
                problems.append("DEBUG must be False in production")
            if self.ALLOWED_HOSTS == ["*"]:
                problems.append("ALLOWED_HOSTS must be set to explicit hostnames in production")
            if self.ALLOWED_ORIGINS == ["*"]:
                problems.append("ALLOWED_ORIGINS must be set to explicit origins in production")
            if "localhost" in self.DATABASE_URL or "127.0.0.1" in self.DATABASE_URL:
                problems.append("DATABASE_URL still points at localhost in production")
            if problems:
                raise ValueError("Invalid production configuration: " + "; ".join(problems))
        return self


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance.

    `lru_cache` ensures the environment/`.env` file is parsed once per
    process and the same instance is reused everywhere via FastAPI's
    dependency injection.
    """
    return Settings()
