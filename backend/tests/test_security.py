"""Tests for security middleware and filename handling."""

from httpx import AsyncClient

from tests.fixtures.pdf_builder import build_pdf

UPLOAD_URL = "/api/v1/resumes/upload"


# -- Request ID / logging / security headers ---------------------------------


async def test_request_id_is_generated_and_echoed(client: AsyncClient) -> None:
    response = await client.get("/health")

    assert "x-request-id" in response.headers
    assert len(response.headers["x-request-id"]) > 0


async def test_request_id_from_client_is_preserved(client: AsyncClient) -> None:
    response = await client.get("/health", headers={"X-Request-ID": "client-supplied-id-123"})

    assert response.headers["x-request-id"] == "client-supplied-id-123"


async def test_response_time_header_present(client: AsyncClient) -> None:
    response = await client.get("/health")

    assert "x-response-time-ms" in response.headers
    assert float(response.headers["x-response-time-ms"]) >= 0


async def test_security_headers_present(client: AsyncClient) -> None:
    response = await client.get("/health")

    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["referrer-policy"] == "no-referrer"


async def test_cors_headers_present_on_cross_origin_request(client: AsyncClient) -> None:
    response = await client.get("/health", headers={"Origin": "https://example.com"})

    assert response.headers.get("access-control-allow-origin") == "*"


# -- Request size limit -------------------------------------------------------


async def test_oversized_request_body_rejected_with_413(client: AsyncClient) -> None:
    # Larger than the default MAX_REQUEST_SIZE (12MB), checked from
    # Content-Length before the request is even routed.
    oversized_content = b"0" * (13 * 1024 * 1024)
    files = {"file": ("huge.pdf", oversized_content, "application/pdf")}

    response = await client.post(UPLOAD_URL, files=files)

    assert response.status_code == 413
    assert response.json()["success"] is False


# -- Filename handling ---------------------------------------------------------


async def test_upload_rejects_path_traversal_filename(client: AsyncClient) -> None:
    files = {"file": ("../../../etc/passwd.pdf", build_pdf("data"), "application/pdf")}

    response = await client.post(UPLOAD_URL, files=files)

    assert response.status_code == 400
    assert response.json()["success"] is False


async def test_upload_sanitizes_unsafe_characters_in_filename(client: AsyncClient) -> None:
    files = {"file": ('resume<>:"|?.pdf', build_pdf("data"), "application/pdf")}

    response = await client.post(UPLOAD_URL, files=files)

    assert response.status_code == 201
    filename = response.json()["filename"]
    assert not any(char in filename for char in '<>:"|?')
