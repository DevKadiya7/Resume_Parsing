"""Integration tests for the parse and parsed-data endpoints."""

from httpx import AsyncClient

from tests.fixtures.pdf_builder import FULL_RESUME_TEXT, build_pdf

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
