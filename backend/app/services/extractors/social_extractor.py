"""Extraction of social/portfolio links from resume text."""

import re

from app.models.social_profile import SocialPlatform
from app.services.extractors.contact_extractor import EMAIL_PATTERN

_URL_TOKEN_PATTERN = re.compile(
    r"(?:https?://)?(?:www\.)?[\w-]+(?:\.[\w-]+)+(?:/[\w./#?=&-]*)?", re.IGNORECASE
)

_EMAIL_PROVIDER_DOMAINS = {
    "gmail.com",
    "yahoo.com",
    "outlook.com",
    "hotmail.com",
    "icloud.com",
    "protonmail.com",
}

_PLATFORM_HINTS: tuple[tuple[str, SocialPlatform], ...] = (
    ("linkedin.com", SocialPlatform.LINKEDIN),
    ("github.com", SocialPlatform.GITHUB),
    ("twitter.com", SocialPlatform.TWITTER),
    ("x.com", SocialPlatform.TWITTER),
    ("medium.com", SocialPlatform.MEDIUM),
)


def extract_social_profiles(text: str) -> list[tuple[SocialPlatform, str]]:
    """Find social/portfolio URLs and classify them by platform.

    Deduplicates by URL (case-insensitive). Email addresses are masked
    out first so an email's domain (e.g. `example.com`) is never
    mistaken for a portfolio link. Any URL-like token that isn't a known
    platform and isn't a common email-provider domain is classified as
    `PORTFOLIO`.
    """
    text_without_emails = EMAIL_PATTERN.sub(" ", text)

    seen: set[str] = set()
    results: list[tuple[SocialPlatform, str]] = []

    for match in _URL_TOKEN_PATTERN.finditer(text_without_emails):
        token = match.group().rstrip(".,;)")
        lowered = token.lower()

        if not re.search(r"[A-Za-z]", token):
            continue  # excludes bare decimals like "8.7" or "3.10"
        if lowered in seen:
            continue

        platform = next((p for hint, p in _PLATFORM_HINTS if hint in lowered), None)
        if platform is None:
            domain = lowered.removeprefix("https://").removeprefix("http://")
            domain = domain.removeprefix("www.").split("/")[0]
            if domain in _EMAIL_PROVIDER_DOMAINS:
                continue
            platform = SocialPlatform.PORTFOLIO

        seen.add(lowered)
        results.append((platform, token))

    return results
