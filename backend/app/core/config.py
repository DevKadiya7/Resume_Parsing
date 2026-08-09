import enum
from functools import lru_cache

from pydantic import model_validator
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

    ALLOWED_HOSTS: str = "*"
    ALLOWED_ORIGINS: str = "*"

    RATE_LIMIT_UPLOAD: str = "20/minute"
    RATE_LIMIT_PARSE: str = "20/minute"

    LOG_FORMAT: str = "text"  # "text" (human-readable console) or "json" (structured)

    # Directory holding the Phase 1 model artifacts (role_classifier.joblib,
    # tfidf_vectorizer.joblib, label_encoder.joblib, metadata.json). Relative
    # paths resolve against the backend root, matching UPLOAD_DIRECTORY.
    ML_ARTIFACTS_DIRECTORY: str = "ml/artifacts"
    # When True, a scikit-learn minor-version difference between training and
    # serving is fatal (503) instead of a warning. Off by default: pickled
    # estimators usually load across patch versions, and refusing to serve is
    # worse than a logged warning for a difference that is normally benign.
    ML_STRICT_VERSION_CHECK: bool = False

    @staticmethod
    def _split_comma_separated(value: str) -> list[str]:
        return [item.strip() for item in value.split(",") if item.strip()]

    @property
    def allowed_hosts(self) -> list[str]:
        return self._split_comma_separated(self.ALLOWED_HOSTS)

    @property
    def allowed_origins(self) -> list[str]:
        return self._split_comma_separated(self.ALLOWED_ORIGINS)

    @model_validator(mode="after")
    def _validate_production_hardening(self) -> "Settings":
        if self.ENVIRONMENT == Environment.PRODUCTION:
            problems = []
            if self.DEBUG:
                problems.append("DEBUG must be False in production")
            if self.ALLOWED_HOSTS.strip() == "*":
                problems.append("ALLOWED_HOSTS must be set to explicit hostnames in production")
            if self.ALLOWED_ORIGINS.strip() == "*":
                problems.append("ALLOWED_ORIGINS must be set to explicit origins in production")
            if "localhost" in self.DATABASE_URL or "127.0.0.1" in self.DATABASE_URL:
                problems.append("DATABASE_URL still points at localhost in production")
            if problems:
                raise ValueError("Invalid production configuration: " + "; ".join(problems))
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
