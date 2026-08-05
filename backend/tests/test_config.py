"""Unit tests for Settings validation (no HTTP/DB involved)."""

import pytest
from pydantic import ValidationError

from app.core.config import Settings

_VALID_PRODUCTION_KWARGS = {
    "ENVIRONMENT": "production",
    "DEBUG": False,
    "ALLOWED_HOSTS": ["api.example.com"],
    "ALLOWED_ORIGINS": ["https://app.example.com"],
    "DATABASE_URL": "postgresql+asyncpg://user:pw@prod-db.internal:5432/resume_db",
}


def test_production_settings_accepts_valid_config() -> None:
    settings = Settings(**_VALID_PRODUCTION_KWARGS)
    assert settings.ENVIRONMENT.value == "production"


def test_production_settings_rejects_debug_true() -> None:
    with pytest.raises(ValidationError, match="DEBUG must be False"):
        Settings(**{**_VALID_PRODUCTION_KWARGS, "DEBUG": True})


def test_production_settings_rejects_wildcard_hosts() -> None:
    with pytest.raises(ValidationError, match="ALLOWED_HOSTS"):
        Settings(**{**_VALID_PRODUCTION_KWARGS, "ALLOWED_HOSTS": ["*"]})


def test_production_settings_rejects_wildcard_origins() -> None:
    with pytest.raises(ValidationError, match="ALLOWED_ORIGINS"):
        Settings(**{**_VALID_PRODUCTION_KWARGS, "ALLOWED_ORIGINS": ["*"]})


def test_production_settings_rejects_localhost_database() -> None:
    with pytest.raises(ValidationError, match="DATABASE_URL"):
        Settings(
            **{
                **_VALID_PRODUCTION_KWARGS,
                "DATABASE_URL": "postgresql+asyncpg://user:pw@localhost:5432/resume_db",
            }
        )


def test_development_settings_allow_wildcards() -> None:
    settings = Settings(ENVIRONMENT="development", DEBUG=True)
    assert settings.ALLOWED_HOSTS == ["*"]
    assert settings.ALLOWED_ORIGINS == ["*"]


def test_allowed_hosts_parses_comma_separated_string() -> None:
    settings = Settings(ALLOWED_HOSTS="a.example.com, b.example.com")
    assert settings.ALLOWED_HOSTS == ["a.example.com", "b.example.com"]
