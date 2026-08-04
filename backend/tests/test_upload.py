"""Tests for POST /api/v1/resumes/upload."""

from httpx import AsyncClient

from tests.conftest import TEN_MB

UPLOAD_URL = "/api/v1/resumes/upload"


async def test_upload_valid_pdf_succeeds(client: AsyncClient) -> None:
    file_content = b"%PDF-1.4\n%mock pdf content for testing\n%%EOF"
    files = {"file": ("resume.pdf", file_content, "application/pdf")}

    response = await client.post(UPLOAD_URL, files=files)

    assert response.status_code == 201
    body = response.json()
    assert body["filename"] == "resume.pdf"
    assert body["status"] == "UPLOADED"
    assert "id" in body
    assert "created_at" in body


async def test_upload_rejects_non_pdf_file(client: AsyncClient) -> None:
    png_content = b"\x89PNG\r\n\x1a\nfake png content"
    files = {"file": ("photo.png", png_content, "image/png")}

    response = await client.post(UPLOAD_URL, files=files)

    assert response.status_code == 400
    body = response.json()
    assert body["success"] is False
    assert body["message"] == "Only PDF files are allowed."


async def test_upload_rejects_file_over_size_limit(client: AsyncClient) -> None:
    oversized_content = b"%PDF-1.4\n" + b"0" * (TEN_MB + 1)
    files = {"file": ("large_resume.pdf", oversized_content, "application/pdf")}

    response = await client.post(UPLOAD_URL, files=files)

    assert response.status_code == 400
    body = response.json()
    assert body["success"] is False
    assert "size" in body["message"].lower()


async def test_upload_rejects_missing_file(client: AsyncClient) -> None:
    response = await client.post(UPLOAD_URL)

    assert response.status_code == 422
    body = response.json()
    assert body["success"] is False
