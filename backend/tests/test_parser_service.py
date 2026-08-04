"""Unit tests for ParserService — pure text-in/structured-data-out, no DB/HTTP."""

import pytest

from app.exceptions.custom_exceptions import (
    CorruptedPdfException,
    EmptyPdfException,
    EncryptedPdfException,
)
from app.models.social_profile import SocialPlatform
from app.services.parser_service import ParserService
from tests.fixtures.pdf_builder import (
    CORRUPTED_PDF_BYTES,
    FULL_RESUME_TEXT,
    RESUME_PAGE_ONE_TEXT,
    RESUME_PAGE_TWO_TEXT,
    RESUME_WITHOUT_EDUCATION_TEXT,
    RESUME_WITHOUT_EXPERIENCE_TEXT,
    build_empty_pdf,
    build_encrypted_pdf,
    build_pdf,
)

parser = ParserService()


def test_parse_valid_resume_extracts_all_sections() -> None:
    pdf_bytes = build_pdf(FULL_RESUME_TEXT)

    result = parser.parse(pdf_bytes)

    assert result.personal_info.full_name == "John Smith"
    assert result.personal_info.email == "john.smith@example.com"
    assert "555-123-4567" in (result.personal_info.phone or "")

    assert {"Python", "FastAPI", "PostgreSQL", "Docker", "AWS", "React"} <= set(result.skills)

    assert len(result.education) == 1
    education = result.education[0]
    assert education.degree == "B.Tech"
    assert education.field_of_study == "Computer Science"
    assert education.institution == "Indian Institute of Technology"
    assert education.grade == "8.7"
    assert education.start_date is not None and education.start_date.year == 2016
    assert education.end_date is not None and education.end_date.year == 2020

    assert len(result.experience) == 1
    experience = result.experience[0]
    assert experience.job_title == "Software Engineer"
    assert experience.company == "Acme Corp"
    assert experience.is_current is True
    assert experience.end_date is None
    assert "payments platform" in (experience.description or "")

    assert len(result.projects) == 1
    project = result.projects[0]
    assert project.name == "Resume Parser"
    assert "Python" in (project.technologies or "")

    assert len(result.certifications) == 1
    certification = result.certifications[0]
    assert certification.name == "AWS Certified Solutions Architect"
    assert certification.issuer == "Amazon Web Services"
    assert certification.date is not None and certification.date.year == 2022

    platforms = {profile.platform for profile in result.social_profiles}
    assert SocialPlatform.LINKEDIN in platforms
    assert SocialPlatform.GITHUB in platforms


def test_parse_resume_without_experience_section() -> None:
    pdf_bytes = build_pdf(RESUME_WITHOUT_EXPERIENCE_TEXT)

    result = parser.parse(pdf_bytes)

    assert result.experience == []
    assert result.personal_info.full_name == "Jane Doe"
    assert len(result.education) == 1
    assert "Java" in result.skills


def test_parse_resume_without_education_section() -> None:
    pdf_bytes = build_pdf(RESUME_WITHOUT_EDUCATION_TEXT)

    result = parser.parse(pdf_bytes)

    assert result.education == []
    assert len(result.experience) == 1
    assert result.experience[0].company == "CloudWorks"


def test_parse_multi_page_resume_preserves_page_order() -> None:
    pdf_bytes = build_pdf(RESUME_PAGE_ONE_TEXT, RESUME_PAGE_TWO_TEXT)

    result = parser.parse(pdf_bytes)

    assert result.personal_info.full_name == "Priya Nair"
    assert len(result.experience) == 1
    assert result.experience[0].company == "DataSoft"

    assert len(result.education) == 1
    assert result.education[0].institution == "Anna University"

    assert len(result.certifications) == 1
    assert result.certifications[0].issuer == "CNCF"


def test_parse_corrupted_pdf_raises() -> None:
    with pytest.raises(CorruptedPdfException):
        parser.parse(CORRUPTED_PDF_BYTES)


def test_parse_encrypted_pdf_raises() -> None:
    pdf_bytes = build_encrypted_pdf(FULL_RESUME_TEXT)

    with pytest.raises(EncryptedPdfException):
        parser.parse(pdf_bytes)


def test_parse_empty_pdf_raises() -> None:
    pdf_bytes = build_empty_pdf()

    with pytest.raises(EmptyPdfException):
        parser.parse(pdf_bytes)


def test_skill_extraction_is_case_insensitive_and_deduplicated() -> None:
    pdf_bytes = build_pdf(
        "Jordan Lee\njordan.lee@example.com\n\nSKILLS\npython, PYTHON, docker, Docker, react\n"
    )

    result = parser.parse(pdf_bytes)

    assert result.skills == sorted(set(result.skills))
    assert result.skills.count("Python") == 1
    assert "Docker" in result.skills
    assert "React" in result.skills


def test_email_extraction() -> None:
    pdf_bytes = build_pdf("Taylor Kim\ntaylor.kim+resume@example.co.uk\n")

    result = parser.parse(pdf_bytes)

    assert result.personal_info.email == "taylor.kim+resume@example.co.uk"


def test_phone_extraction_with_country_code() -> None:
    pdf_bytes = build_pdf("Rahul Verma\nrahul.verma@example.com\n+91 9876543210\n")

    result = parser.parse(pdf_bytes)

    digits = "".join(char for char in (result.personal_info.phone or "") if char.isdigit())
    assert digits == "919876543210"
