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

# Common real-world TLDs/domain suffixes. Used to reject "word.word"
# tokens that merely *look* URL-shaped — abbreviations like "B.E", "L.D.",
# or a bare framework mention like "React.js" — when the token wasn't
# already given an explicit `http(s)://`/`www.` prefix (a strong signal on
# its own that it really is a URL, checked separately).
_PLAUSIBLE_TLDS = frozenset(
    {
        "com",
        "io",
        "dev",
        "net",
        "org",
        "me",
        "in",
        "co",
        "app",
        "ai",
        "tech",
        "info",
        "biz",
        "edu",
        "gov",
        "us",
        "uk",
        "ca",
        "id",
    }
)

_PLATFORM_HINTS: tuple[tuple[str, SocialPlatform], ...] = (
    ("linkedin.com", SocialPlatform.LINKEDIN),
    ("github.com", SocialPlatform.GITHUB),
    ("twitter.com", SocialPlatform.TWITTER),
    ("x.com", SocialPlatform.TWITTER),
    ("medium.com", SocialPlatform.MEDIUM),
    # LeetCode/HackerRank/personal-website links don't have a dedicated
    # `SocialPlatform` value (adding one would be a database schema
    # change, out of scope here) — they're still recognized and kept,
    # just bucketed under the existing PORTFOLIO value rather than
    # silently dropped or misclassified as something else.
    ("leetcode.com", SocialPlatform.PORTFOLIO),
    ("hackerrank.com", SocialPlatform.PORTFOLIO),
)


def _has_plausible_tld(token: str) -> bool:
    domain = token.split("/")[0]
    tld = domain.rsplit(".", 1)[-1].lower()
    return tld in _PLAUSIBLE_TLDS


def extract_social_profiles(text: str) -> list[tuple[SocialPlatform, str]]:
    """Find social/portfolio URLs and classify them by platform.

    Deduplicates by URL (case-insensitive — including a bare-domain vs.
    `https://`-prefixed mention of the same link). Email addresses are
    masked out first so an email's domain (e.g. `example.com`) is never
    mistaken for a portfolio link. A token without an explicit
    `http(s)://`/`www.` prefix must also end in a plausible TLD to be
    accepted, which is what keeps incidental "word.word" text — degree
    abbreviations like "B.E"/"L.D.", or "React.js" mentioned as a
    technology — from being misread as portfolio links.
    """
    text_without_emails = EMAIL_PATTERN.sub(" ", text)

    seen: set[str] = set()
    results: list[tuple[SocialPlatform, str]] = []

    for match in _URL_TOKEN_PATTERN.finditer(text_without_emails):
        token = match.group().rstrip(".,;)")
        lowered = token.lower()

        if not re.search(r"[A-Za-z]", token):
            continue  # excludes bare decimals like "8.7" or "3.10"

        has_explicit_prefix = lowered.startswith(("http://", "https://", "www."))
        if not has_explicit_prefix and not _has_plausible_tld(lowered):
            continue

        domain = lowered.removeprefix("https://").removeprefix("http://")
        domain = domain.removeprefix("www.").split("/")[0]
        dedup_key = domain  # "linkedin.com/in/x" and "https://linkedin.com/in/x" dedupe together
        if dedup_key in seen:
            continue

        platform = next((p for hint, p in _PLATFORM_HINTS if hint in lowered), None)
        if platform is None:
            if domain in _EMAIL_PROVIDER_DOMAINS:
                continue
            platform = SocialPlatform.PORTFOLIO

        seen.add(dedup_key)
        results.append((platform, token))

    return results
