"""Tests for the top-level meta endpoints."""

from httpx import AsyncClient


async def test_root_returns_service_message(client: AsyncClient) -> None:
    response = await client.get("/")

    assert response.status_code == 200
    assert response.json() == {"message": "Resume Parsing Service"}


async def test_health_returns_healthy(client: AsyncClient) -> None:
    response = await client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}
