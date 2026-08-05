"""Edge-case tests: large/tiny/unicode resumes, duplicate and concurrent uploads."""

import asyncio

from httpx import AsyncClient

from tests.fixtures.pdf_builder import build_pdf

UPLOAD_URL = "/api/v1/resumes/upload"


async def test_upload_and_parse_large_resume(client: AsyncClient) -> None:
    """A resume spanning many pages with a large number of experience entries.

    `build_pdf` renders each positional argument onto its own page and
    clips content that overflows a page's textbox, so a large document
    must be pre-paginated — one call per page — the same way a real
    multi-page PDF would be, rather than handed to `build_pdf` as one
    giant single-page string.
    """
    header = ["Jordan Lee", "jordan.lee@example.com", "+1 555-000-1111", "", "EXPERIENCE"]
    entries = []
    for i in range(120):
        entries += [
            f"Senior Engineer {i} at Company{i} Inc",
            "Jan 2010 - Dec 2011",
            f"Worked on project number {i} across the platform team.",
            "",
        ]

    lines_per_page = 40
    all_lines = header + entries
    pages = [
        "\n".join(all_lines[i : i + lines_per_page])
        for i in range(0, len(all_lines), lines_per_page)
    ]

    files = {"file": ("large_resume.pdf", build_pdf(*pages), "application/pdf")}
    upload_response = await client.post(UPLOAD_URL, files=files)
    assert upload_response.status_code == 201
    resume_id = upload_response.json()["id"]

    parse_response = await client.post(f"/api/v1/resumes/{resume_id}/parse")
    assert parse_response.status_code == 200
    parsed = parse_response.json()["parsed"]
    assert parsed["personal_info"]["full_name"] == "Jordan Lee"
    assert len(parsed["experience"]) > 0


async def test_upload_and_parse_very_small_resume(client: AsyncClient) -> None:
    """A minimal resume with just a name and email — no sections at all."""
    tiny_text = "Sam Rivera\nsam.rivera@example.com"

    files = {"file": ("tiny_resume.pdf", build_pdf(tiny_text), "application/pdf")}
    upload_response = await client.post(UPLOAD_URL, files=files)
    assert upload_response.status_code == 201
    resume_id = upload_response.json()["id"]

    parse_response = await client.post(f"/api/v1/resumes/{resume_id}/parse")
    assert parse_response.status_code == 200
    parsed = parse_response.json()["parsed"]
    assert parsed["personal_info"]["email"] == "sam.rivera@example.com"
    assert parsed["education"] == []
    assert parsed["experience"] == []


async def test_upload_and_parse_unicode_resume(client: AsyncClient) -> None:
    """Non-ASCII names, accented characters, and non-Latin script content."""
    unicode_text = (
        "Élodie Müller\n"
        "elodie.muller@example.com\n"
        "+33 6 12 34 56 78\n\n"
        "SKILLS\n"
        "Python, Docker\n\n"
        "EDUCATION\n"
        "Université Paris-Saclay\n"
        "Master en Informatique\n"
        "2018 - 2020\n\n"
        "SUMMARY\n"
        "エンジニア | ソフトウェア開発者 — over 5 years building backend systems.\n"
    )

    files = {"file": ("résumé_日本語.pdf", build_pdf(unicode_text), "application/pdf")}
    upload_response = await client.post(UPLOAD_URL, files=files)
    assert upload_response.status_code == 201
    body = upload_response.json()
    assert "resum" in body["filename"].lower() or "日本語" in body["filename"]
    resume_id = body["id"]

    parse_response = await client.post(f"/api/v1/resumes/{resume_id}/parse")
    assert parse_response.status_code == 200
    parsed = parse_response.json()["parsed"]
    assert parsed["personal_info"]["email"] == "elodie.muller@example.com"
    assert "Python" in parsed["skills"]


async def test_duplicate_upload_same_content_allowed(client: AsyncClient) -> None:
    """Uploading the same file twice is allowed — each gets its own UUID-based record."""
    content = build_pdf("Taylor Kim\ntaylor.kim@example.com")
    files = {"file": ("resume.pdf", content, "application/pdf")}

    first = await client.post(UPLOAD_URL, files=files)
    second = await client.post(
        UPLOAD_URL, files={"file": ("resume.pdf", content, "application/pdf")}
    )

    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["id"] != second.json()["id"]
    assert first.json()["filename"] == second.json()["filename"] == "resume.pdf"


async def test_concurrent_upload_simulation(client: AsyncClient) -> None:
    """Several uploads fired concurrently should all succeed with distinct IDs."""

    async def _upload(index: int):
        content = build_pdf(f"Candidate {index}\ncandidate{index}@example.com")
        files = {"file": (f"candidate_{index}.pdf", content, "application/pdf")}
        return await client.post(UPLOAD_URL, files=files)

    responses = await asyncio.gather(*(_upload(i) for i in range(10)))

    assert all(response.status_code == 201 for response in responses)
    ids = {response.json()["id"] for response in responses}
    assert len(ids) == 10
