"""Shared pytest fixtures.

Tests run fully in-process against an in-memory SQLite database and a
temporary upload directory — no Docker/Postgres required. This is done
via FastAPI dependency overrides (`get_db`, `get_settings`) rather than
by pointing the real app config at SQLite, so the production wiring in
`app.db.database` / `app.core.config` is exercised unmodified.
"""

from collections.abc import AsyncGenerator

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.core.config import Settings, get_settings
from app.db.database import Base, get_db
from app.main import app

TEN_MB = 10 * 1024 * 1024

test_engine = create_async_engine(
    "sqlite+aiosqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSessionLocal = async_sessionmaker(bind=test_engine, class_=AsyncSession, expire_on_commit=False)


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
