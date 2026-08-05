"""Integration tests for the resume listing/search/detail/statistics/delete/download APIs."""

from pathlib import Path

from httpx import AsyncClient

from tests.fixtures.management_pdfs import ALICE_TEXT, BOB_TEXT, CAROL_TEXT
from tests.fixtures.pdf_builder import build_pdf

UPLOAD_URL = "/api/v1/resumes/upload"


async def _upload(client: AsyncClient, text: str, filename: str) -> str:
    files = {"file": (filename, build_pdf(text), "application/pdf")}
    response = await client.post(UPLOAD_URL, files=files)
    assert response.status_code == 201
    return response.json()["id"]


async def _upload_and_parse(client: AsyncClient, text: str, filename: str) -> str:
    resume_id = await _upload(client, text, filename)
    response = await client.post(f"/api/v1/resumes/{resume_id}/parse")
    assert response.status_code == 200
    return resume_id


async def _seed_three_resumes(client: AsyncClient) -> dict[str, str]:
    """Alice and Bob are parsed; Carol is uploaded but never parsed."""
    alice_id = await _upload_and_parse(client, ALICE_TEXT, "alice.pdf")
    bob_id = await _upload_and_parse(client, BOB_TEXT, "bob.pdf")
    carol_id = await _upload(client, CAROL_TEXT, "carol.pdf")
    return {"alice": alice_id, "bob": bob_id, "carol": carol_id}


# -- Listing / pagination / sorting -----------------------------------------


async def test_list_resumes_pagination(client: AsyncClient) -> None:
    await _seed_three_resumes(client)

    response = await client.get("/api/v1/resumes?page=1&page_size=2")

    assert response.status_code == 200
    body = response.json()
    assert body["page"] == 1
    assert body["page_size"] == 2
    assert body["total"] == 3
    assert len(body["items"]) == 2


async def test_list_resumes_sort_by_filename_ascending(client: AsyncClient) -> None:
    await _seed_three_resumes(client)

    response = await client.get("/api/v1/resumes?sort=filename&order=asc&page_size=10")

    assert response.status_code == 200
    filenames = [item["filename"] for item in response.json()["items"]]
    assert filenames == sorted(filenames)


async def test_list_resumes_filter_parsed_true(client: AsyncClient) -> None:
    await _seed_three_resumes(client)

    response = await client.get("/api/v1/resumes?parsed=true&page_size=10")

    body = response.json()
    assert body["total"] == 2
    assert all(item["is_parsed"] for item in body["items"])


async def test_list_resumes_filter_parsed_false(client: AsyncClient) -> None:
    await _seed_three_resumes(client)

    response = await client.get("/api/v1/resumes?parsed=false&page_size=10")

    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["filename"] == "carol.pdf"


async def test_list_resumes_filter_has_experience(client: AsyncClient) -> None:
    await _seed_three_resumes(client)

    response = await client.get("/api/v1/resumes?has_experience=true&page_size=10")

    body = response.json()
    filenames = {item["filename"] for item in body["items"]}
    assert filenames == {"alice.pdf", "bob.pdf"}


async def test_list_resumes_filter_has_projects(client: AsyncClient) -> None:
    await _seed_three_resumes(client)

    response = await client.get("/api/v1/resumes?has_projects=true&page_size=10")

    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["filename"] == "alice.pdf"


async def test_list_resumes_minimum_experience(client: AsyncClient) -> None:
    await _seed_three_resumes(client)

    response = await client.get("/api/v1/resumes?minimum_experience=1&page_size=10")

    body = response.json()
    filenames = {item["filename"] for item in body["items"]}
    assert filenames == {"alice.pdf", "bob.pdf"}


# -- Validation ---------------------------------------------------------------


async def test_list_resumes_rejects_negative_page(client: AsyncClient) -> None:
    response = await client.get("/api/v1/resumes?page=-1")
    assert response.status_code == 422


async def test_list_resumes_rejects_invalid_page_size(client: AsyncClient) -> None:
    response = await client.get("/api/v1/resumes?page_size=0")
    assert response.status_code == 422


async def test_list_resumes_rejects_unknown_sort_field(client: AsyncClient) -> None:
    response = await client.get("/api/v1/resumes?sort=bogus_field")
    assert response.status_code == 422


async def test_list_resumes_rejects_unknown_query_param(client: AsyncClient) -> None:
    response = await client.get("/api/v1/resumes?not_a_real_filter=true")

    assert response.status_code == 400
    assert response.json()["success"] is False


async def test_get_resume_rejects_invalid_uuid(client: AsyncClient) -> None:
    response = await client.get("/api/v1/resumes/not-a-valid-uuid")
    assert response.status_code == 422


async def test_get_resume_not_found(client: AsyncClient) -> None:
    response = await client.get("/api/v1/resumes/00000000-0000-0000-0000-000000000000")

    assert response.status_code == 404
    assert response.json()["success"] is False


# -- Single resume / details ---------------------------------------------------


async def test_get_single_resume(client: AsyncClient) -> None:
    ids = await _seed_three_resumes(client)

    response = await client.get(f"/api/v1/resumes/{ids['alice']}")

    assert response.status_code == 200
    body = response.json()
    assert body["filename"] == "alice.pdf"
    assert body["is_parsed"] is True
    assert "created_at" in body and "updated_at" in body


async def test_get_resume_details_nested_shape(client: AsyncClient) -> None:
    ids = await _seed_three_resumes(client)

    response = await client.get(f"/api/v1/resumes/{ids['alice']}/details")

    assert response.status_code == 200
    body = response.json()
    assert body["resume"]["filename"] == "alice.pdf"
    assert body["parsed"]["personal_info"]["full_name"] == "Alice Johnson"
    assert "Python" in body["parsed"]["skills"]
    assert len(body["parsed"]["education"]) == 1
    assert len(body["parsed"]["certifications"]) == 1


async def test_get_resume_details_unparsed_returns_null_parsed(client: AsyncClient) -> None:
    ids = await _seed_three_resumes(client)

    response = await client.get(f"/api/v1/resumes/{ids['carol']}/details")

    assert response.status_code == 200
    body = response.json()
    assert body["resume"]["is_parsed"] is False
    assert body["parsed"] is None


# -- Search ---------------------------------------------------------------------


async def test_search_by_skill(client: AsyncClient) -> None:
    # Carol is uploaded but never parsed, so she has no Skill rows at all —
    # only Alice (parsed, lists Python) should match.
    await _seed_three_resumes(client)

    response = await client.get("/api/v1/resumes/search?skill=python")

    body = response.json()
    filenames = {item["filename"] for item in body["items"]}
    assert filenames == {"alice.pdf"}


async def test_search_by_company(client: AsyncClient) -> None:
    await _seed_three_resumes(client)

    response = await client.get("/api/v1/resumes/search?company=google")

    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["filename"] == "alice.pdf"


async def test_search_by_name_partial_case_insensitive(client: AsyncClient) -> None:
    await _seed_three_resumes(client)

    response = await client.get("/api/v1/resumes/search?name=ALICE")

    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["filename"] == "alice.pdf"


async def test_search_by_email_domain(client: AsyncClient) -> None:
    # Carol is uploaded but never parsed, so she has no PersonalInfo row —
    # only Alice and Bob (parsed) should match.
    await _seed_three_resumes(client)

    response = await client.get("/api/v1/resumes/search?email=example.com")

    assert response.json()["total"] == 2


async def test_search_multiple_filters_combined(client: AsyncClient) -> None:
    await _seed_three_resumes(client)

    response = await client.get("/api/v1/resumes/search?skill=python&company=google")

    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["filename"] == "alice.pdf"


async def test_search_by_college(client: AsyncClient) -> None:
    await _seed_three_resumes(client)

    response = await client.get("/api/v1/resumes/search?college=stanford")

    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["filename"] == "bob.pdf"


async def test_search_by_degree(client: AsyncClient) -> None:
    await _seed_three_resumes(client)

    response = await client.get("/api/v1/resumes/search?degree=MBA")

    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["filename"] == "bob.pdf"


async def test_search_rejects_unknown_query_param(client: AsyncClient) -> None:
    response = await client.get("/api/v1/resumes/search?location=nowhere")

    assert response.status_code == 400
    assert response.json()["success"] is False


# -- Statistics -------------------------------------------------------------------


async def test_statistics(client: AsyncClient) -> None:
    await _seed_three_resumes(client)

    response = await client.get("/api/v1/resumes/statistics")

    assert response.status_code == 200
    body = response.json()
    assert body["total_resumes"] == 3
    assert body["parsed"] == 2
    assert body["pending"] == 1

    skill_names = {entry["skill"] for entry in body["top_skills"]}
    assert "Python" in skill_names

    company_names = {entry["company"] for entry in body["top_companies"]}
    assert "Google" in company_names


# -- Delete -----------------------------------------------------------------------


async def test_delete_resume_removes_record_and_file(client: AsyncClient, tmp_path: Path) -> None:
    # Files are stored under uploads/<year>/<month>/, not flat in tmp_path.
    ids = await _seed_three_resumes(client)
    resume_id = ids["alice"]

    stored_files_before = list(tmp_path.rglob("*.pdf"))
    assert len(stored_files_before) == 3

    response = await client.delete(f"/api/v1/resumes/{resume_id}")

    assert response.status_code == 204

    get_response = await client.get(f"/api/v1/resumes/{resume_id}")
    assert get_response.status_code == 404

    stored_files_after = list(tmp_path.rglob("*.pdf"))
    assert len(stored_files_after) == 2


async def test_delete_resume_not_found(client: AsyncClient) -> None:
    response = await client.delete("/api/v1/resumes/00000000-0000-0000-0000-000000000000")

    assert response.status_code == 404
    assert response.json()["success"] is False


# -- Download ---------------------------------------------------------------------


async def test_download_resume(client: AsyncClient) -> None:
    ids = await _seed_three_resumes(client)

    response = await client.get(f"/api/v1/resumes/{ids['alice']}/download")

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert "alice.pdf" in response.headers["content-disposition"]
    assert response.content.startswith(b"%PDF")


async def test_download_resume_not_found(client: AsyncClient) -> None:
    response = await client.get("/api/v1/resumes/00000000-0000-0000-0000-000000000000/download")

    assert response.status_code == 404
    assert response.json()["success"] is False


async def test_download_after_delete_returns_404(client: AsyncClient) -> None:
    ids = await _seed_three_resumes(client)
    resume_id = ids["alice"]

    delete_response = await client.delete(f"/api/v1/resumes/{resume_id}")
    assert delete_response.status_code == 204

    response = await client.get(f"/api/v1/resumes/{resume_id}/download")

    assert response.status_code == 404
    assert response.json()["success"] is False
