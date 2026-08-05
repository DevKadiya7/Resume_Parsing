"""Regression tests for the extraction-quality fixes.

Each test targets one specific bug found by diagnosing a real resume's
raw PyMuPDF text: invisible zero-width characters breaking section
detection, headings with extra words not matching, the name heuristic
picking a heading word, skills-lines being misread as an address,
false-positive "portfolio" links from bare word.word text, hyperlink
annotations never reaching the text layer, and bullet-packed
multi-entry sections with no blank lines between entries.
"""

from app.services.extractors import (
    block_splitter,
    contact_extractor,
    education_extractor,
    experience_extractor,
    project_extractor,
    section_splitter,
    social_extractor,
    text_extractor,
)
from app.services.parser_service import ParserService
from tests.fixtures.pdf_builder import build_pdf, build_pdf_with_link

ZWSP = "​"


# -- Invisible characters (the root cause) -----------------------------------


def test_clean_text_strips_zero_width_space() -> None:
    dirty = f"PROJECTS{ZWSP}\n\nSome text"
    assert "PROJECTS" in text_extractor.clean_text(dirty)
    assert ZWSP not in text_extractor.clean_text(dirty)


def test_clean_text_strips_bom_and_word_joiner() -> None:
    dirty = "Kadiya Dev﻿\nheading⁠text"
    cleaned = text_extractor.clean_text(dirty)
    assert "﻿" not in cleaned
    assert "⁠" not in cleaned


def test_section_splitter_detects_header_with_trailing_zero_width_space() -> None:
    # Simulates the exact real-world bug: a header line that would match
    # an alias exactly, except for an invisible character PyMuPDF left in.
    text = f"Some Name\n\nPROJECTS{ZWSP}\n\nBuilt a thing."
    cleaned = text_extractor.clean_text(text)
    sections = section_splitter.split_sections(cleaned)
    assert "Built a thing." in sections["projects"]
    assert "PROJECTS" not in sections["header"]


# -- Fuzzy section-header matching -------------------------------------------


def test_section_splitter_matches_heading_with_extra_words() -> None:
    text = "Name\n\nWORK EXPERIENCE & INTERNSHIP\n\nDid some work."
    sections = section_splitter.split_sections(text)
    assert "Did some work." in sections["experience"]


def test_section_splitter_does_not_misread_prose_mentioning_experience() -> None:
    text = (
        "Name\n\nEXPERIENCE\n\nSoftware Engineer at Acme\n"
        "Experience in building scalable systems using Python and Django "
        "across several long-running production services.\n"
    )
    sections = section_splitter.split_sections(text)
    # The prose sentence must stay inside "experience", not be misread as
    # a second, new section boundary that resets to some other section.
    assert "Experience in building scalable systems" in sections["experience"]


def test_section_splitter_recognizes_expanded_aliases() -> None:
    text = (
        "Name\n\nQUALIFICATION\n\nB.Tech\n\n"
        "INTERNSHIP\n\nIntern at Acme\n\n"
        "PORTFOLIO\n\nCool Project\n\n"
        "LICENSES\n\nAWS Certified\n"
    )
    sections = section_splitter.split_sections(text)
    assert "B.Tech" in sections["education"]
    assert "Intern at Acme" in sections["experience"]
    assert "Cool Project" in sections["projects"]
    assert "AWS Certified" in sections["certifications"]


# -- Name extraction: heading blocklist + prominent-line + scoping ----------


def test_extract_name_ignores_heading_words() -> None:
    # No plausible name line at all before contact info — must not fall
    # back to a heading word looking vaguely name-shaped.
    header = "Skills\nMachine Learning\nkadiya@example.com"
    assert contact_extractor.extract_name(header) is None


def test_extract_name_prefers_prominent_line_when_valid() -> None:
    header = "Computer Engineering\nkadiya@example.com"
    assert contact_extractor.extract_name(header, prominent_line="Kadiya Dev") == "Kadiya Dev"


def test_extract_name_rejects_heading_word_as_prominent_line() -> None:
    header = "Kadiya Dev\nkadiya@example.com"
    # A bogus "prominent line" that happens to be a heading word must be
    # rejected, falling through to the positional heuristic instead.
    assert contact_extractor.extract_name(header, prominent_line="Skills") == "Kadiya Dev"


def test_extract_name_stops_scanning_at_contact_info() -> None:
    # "Computer Engineering" (2 title-case words) would match the name
    # shape regex, but it appears after the phone number and must be
    # ignored — a name never appears after contact info.
    header = "Kadiya Dev\n+91 8320364436\nComputer Engineering"
    assert contact_extractor.extract_name(header) == "Kadiya Dev"


# -- Address extraction: reject skills/labelled lines ------------------------


def test_extract_address_rejects_labelled_skills_line() -> None:
    header = "Frontend: React.js, HTML5, CSS3, JavaScript"
    assert contact_extractor.extract_address(header) is None


def test_extract_address_accepts_city_state_line() -> None:
    header = "San Francisco, CA 94105"
    assert contact_extractor.extract_address(header) == "San Francisco, CA 94105"


def test_extract_address_accepts_street_keyword_line() -> None:
    header = "221B Baker Street, London"
    assert contact_extractor.extract_address(header) == "221B Baker Street, London"


# -- Social link false positives + hyperlink annotations ---------------------


def test_social_extractor_rejects_abbreviation_false_positives() -> None:
    text = "Computer Engineering\nB.E\nL.D. College Of Engineering\nReact.js"
    assert social_extractor.extract_social_profiles(text) == []


def test_social_extractor_accepts_bare_domain_with_plausible_tld() -> None:
    from app.models.social_profile import SocialPlatform

    results = social_extractor.extract_social_profiles("myportfolio.dev")
    assert results == [(SocialPlatform.PORTFOLIO, "myportfolio.dev")]


def test_social_extractor_deduplicates_bare_and_prefixed_same_domain() -> None:
    text = "github.com/janedoe and also https://github.com/janedoe"
    results = social_extractor.extract_social_profiles(text)
    assert len(results) == 1


def test_parser_service_picks_up_hyperlink_annotation_urls() -> None:
    """A resume's real LinkedIn/GitHub URLs are frequently attached as a
    clickable link annotation on anchor text like "LinkedIn", never
    appearing in the visible text layer at all.
    """
    text = "Jane Doe\njane@example.com\nLinkedIn | GitHub\n"
    pdf_bytes = build_pdf_with_link(
        text, link_uri="https://www.linkedin.com/in/janedoe", link_text="LinkedIn"
    )

    parsed = ParserService().parse(pdf_bytes)

    from app.models.social_profile import SocialPlatform

    assert any(
        profile.platform == SocialPlatform.LINKEDIN and "janedoe" in profile.url
        for profile in parsed.social_profiles
    )


# -- Bullet-packed multi-entry sections (no blank lines between entries) ----


def test_block_splitter_splits_on_bullets_when_no_blank_lines() -> None:
    section = "• Project One\nDid a thing.\n• Project Two\nDid another thing.\n"
    blocks = block_splitter.split_entry_blocks(section)
    assert len(blocks) == 2
    assert blocks[0].startswith("• Project One")
    assert blocks[1].startswith("• Project Two")


def test_project_extractor_handles_bullet_packed_projects() -> None:
    section = (
        "• Real Estate Project\n"
        "Built a price predictor using Python and FastAPI.\n"
        "• Crypto Tracker\n"
        "Built a real-time dashboard using React and SQL.\n"
    )
    entries = project_extractor.extract_projects(section)
    assert len(entries) == 2
    assert entries[0]["name"] == "Real Estate Project"
    assert entries[1]["name"] == "Crypto Tracker"


def test_experience_extractor_handles_en_dash_separator() -> None:
    section = "Data Analytics Intern – ADS Foundation\nJan 2024 - Present\nDid analytics work.\n"
    entries = experience_extractor.extract_experience(section)
    assert len(entries) == 1
    assert entries[0]["job_title"] == "Data Analytics Intern"
    assert entries[0]["company"] == "ADS Foundation"


# -- Education: header fallback + adjacent-line field-of-study ---------------


def test_education_extractor_finds_field_of_study_on_adjacent_line() -> None:
    block = "Computer Engineering\nB.E\nL.D. College Of Engineering"
    entries = education_extractor.extract_education(block)
    assert len(entries) == 1
    assert entries[0]["degree"] == "B.E"
    assert entries[0]["field_of_study"] == "Computer Engineering"
    assert entries[0]["institution"] == "L.D. College Of Engineering"


def test_parser_service_falls_back_to_header_for_education_when_no_section() -> None:
    """No literal "Education" heading at all — degree/institution sit
    directly in the header, a common compact-resume layout.
    """
    text = (
        "Jane Doe\njane@example.com\nComputer Engineering\nB.E\nXYZ College\n\n"
        "PROJECTS\n\nSomething built.\n"
    )
    pdf_bytes = build_pdf(text)

    parsed = ParserService().parse(pdf_bytes)

    assert len(parsed.education) == 1
    assert parsed.education[0].degree == "B.E"
    assert parsed.education[0].institution == "XYZ College"
