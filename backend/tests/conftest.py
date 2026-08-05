"""Shared pytest fixtures.

Tests run fully in-process against an in-memory SQLite database and a
temporary upload directory — no Docker/Postgres required. This is done
via FastAPI dependency overrides (`get_db`, `get_settings`) rather than
by pointing the real app config at SQLite, so the production wiring in
`app.db.database` / `app.core.config` is exercised unmodified.
"""

import os
from collections.abc import AsyncGenerator

# Rate limits are baked into the route decorators at import time (see
# app/api/v1/resume.py), so they must be widened via real environment
# variables *before* `app.main` is imported — a per-test dependency
# override (as used for the DB/upload-directory below) is too late to
# affect them. Without this, the full test suite's upload/parse call
# volume would trip the default rate limit and fail unrelated tests.
os.environ.setdefault("RATE_LIMIT_UPLOAD", "100000/minute")
os.environ.setdefault("RATE_LIMIT_PARSE", "100000/minute")

import tempfile  # noqa: E402

import pytest_asyncio  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402
from sqlalchemy.ext.asyncio import (  # noqa: E402
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import Settings, get_settings  # noqa: E402
from app.db.database import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402

TEN_MB = 10 * 1024 * 1024

# A file-based SQLite DB (not `:memory:` + StaticPool) so concurrent-upload
# tests exercise genuinely separate connections, the same way pool-backed
# Postgres does in production. A single shared `:memory:` connection can
# only run one transaction at a time and raises "cannot commit transaction
# - SQL statements in progress" the moment two requests overlap.
_tmp_db_fd, _tmp_db_path = tempfile.mkstemp(suffix=".db")
os.close(_tmp_db_fd)

test_engine = create_async_engine(
    f"sqlite+aiosqlite:///{_tmp_db_path}",
    connect_args={"check_same_thread": False},
)
TestSessionLocal = async_sessionmaker(
    bind=test_engine, class_=AsyncSession, expire_on_commit=False
)


async def _override_get_db() -> AsyncGenerator[AsyncSession, None]:
    async with TestSessionLocal() as session:
        yield session


@pytest_asyncio.fixture
async def client(tmp_path) -> AsyncGenerator[AsyncClient, None]:
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    def _override_get_settings() -> Settings:
        return Settings(
            APP_NAME="Resume Parsing Service",
            DEBUG=False,
            DATABASE_URL="sqlite+aiosqlite:///:memory:",
            UPLOAD_DIRECTORY=str(tmp_path),
            MAX_FILE_SIZE=TEN_MB,
        )

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_settings] = _override_get_settings

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as async_client:
        yield async_client

    app.dependency_overrides.clear()
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
