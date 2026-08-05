"""Integration tests for the parse and parsed-data endpoints."""

from pathlib import Path

from httpx import AsyncClient

from tests.fixtures.pdf_builder import (
    CORRUPTED_PDF_BYTES,
    FULL_RESUME_TEXT,
    build_empty_pdf,
    build_encrypted_pdf,
    build_pdf,
)

UPLOAD_URL = "/api/v1/resumes/upload"


async def _upload_resume(
    client: AsyncClient, pdf_bytes: bytes, filename: str = "resume.pdf"
) -> str:
    files = {"file": (filename, pdf_bytes, "application/pdf")}
    response = await client.post(UPLOAD_URL, files=files)
    assert response.status_code == 201
    return response.json()["id"]


async def test_parse_uploaded_resume_succeeds(client: AsyncClient) -> None:
    resume_id = await _upload_resume(client, build_pdf(FULL_RESUME_TEXT))

    response = await client.post(f"/api/v1/resumes/{resume_id}/parse")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["resume_id"] == resume_id
    assert body["parsed"]["personal_info"]["full_name"] == "John Smith"
    assert "Python" in body["parsed"]["skills"]
    assert len(body["parsed"]["education"]) == 1
    assert len(body["parsed"]["experience"]) == 1


async def test_get_parsed_data_after_parsing(client: AsyncClient) -> None:
    resume_id = await _upload_resume(client, build_pdf(FULL_RESUME_TEXT))
    await client.post(f"/api/v1/resumes/{resume_id}/parse")

    response = await client.get(f"/api/v1/resumes/{resume_id}/parsed")

    assert response.status_code == 200
    body = response.json()
    assert body["parsed"]["personal_info"]["email"] == "john.smith@example.com"


async def test_get_parsed_data_before_parsing_returns_404(client: AsyncClient) -> None:
    resume_id = await _upload_resume(client, build_pdf(FULL_RESUME_TEXT))

    response = await client.get(f"/api/v1/resumes/{resume_id}/parsed")

    assert response.status_code == 404
    assert response.json()["success"] is False


async def test_duplicate_parse_returns_409(client: AsyncClient) -> None:
    resume_id = await _upload_resume(client, build_pdf(FULL_RESUME_TEXT))
    first = await client.post(f"/api/v1/resumes/{resume_id}/parse")
    assert first.status_code == 200

    second = await client.post(f"/api/v1/resumes/{resume_id}/parse")

    assert second.status_code == 409
    assert second.json()["success"] is False


async def test_parse_nonexistent_resume_returns_404(client: AsyncClient) -> None:
    response = await client.post("/api/v1/resumes/00000000-0000-0000-0000-000000000000/parse")

    assert response.status_code == 404
    assert response.json()["success"] is False


# -- Error paths, exercised through the real HTTP endpoint rather than only
# -- at the ParserService unit level (see test_parser_service.py) --------


async def test_parse_corrupted_pdf_returns_422(client: AsyncClient) -> None:
    resume_id = await _upload_resume(client, CORRUPTED_PDF_BYTES, filename="corrupted.pdf")

    response = await client.post(f"/api/v1/resumes/{resume_id}/parse")

    assert response.status_code == 422
    assert response.json()["success"] is False


async def test_parse_encrypted_pdf_returns_422(client: AsyncClient) -> None:
    resume_id = await _upload_resume(
        client, build_encrypted_pdf("secret content"), filename="encrypted.pdf"
    )

    response = await client.post(f"/api/v1/resumes/{resume_id}/parse")

    assert response.status_code == 422
    assert response.json()["success"] is False


async def test_parse_empty_pdf_returns_422(client: AsyncClient) -> None:
    resume_id = await _upload_resume(client, build_empty_pdf(), filename="empty.pdf")

    response = await client.post(f"/api/v1/resumes/{resume_id}/parse")

    assert response.status_code == 422
    assert response.json()["success"] is False


async def test_parse_returns_500_when_stored_file_is_missing_from_disk(
    client: AsyncClient, tmp_path: Path
) -> None:
    """The DB record exists but its PDF has vanished from disk — e.g. a
    backup-restore gap or out-of-band deletion — distinct from any
    application-level error path.
    """
    resume_id = await _upload_resume(client, build_pdf(FULL_RESUME_TEXT))
    for stored_file in tmp_path.rglob("*.pdf"):
        stored_file.unlink()

    response = await client.post(f"/api/v1/resumes/{resume_id}/parse")

    assert response.status_code == 500
    assert response.json()["success"] is False
