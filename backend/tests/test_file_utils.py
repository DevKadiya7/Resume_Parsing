"""Unit tests for filename safety helpers (no HTTP/DB involved)."""

from app.utils.file_utils import is_dangerous_filename, sanitize_original_filename


def test_is_dangerous_filename_flags_null_byte() -> None:
    assert is_dangerous_filename("resume\x00.pdf") is True


def test_is_dangerous_filename_flags_path_traversal() -> None:
    assert is_dangerous_filename("../../etc/passwd.pdf") is True


def test_is_dangerous_filename_flags_absolute_path() -> None:
    assert is_dangerous_filename("/etc/passwd.pdf") is True


def test_is_dangerous_filename_allows_normal_name() -> None:
    assert is_dangerous_filename("jane_doe_resume.pdf") is False


def test_is_dangerous_filename_allows_unicode_name() -> None:
    assert is_dangerous_filename("résumé_日本語.pdf") is False


def test_sanitize_strips_directory_components() -> None:
    assert sanitize_original_filename("folder/resume.pdf") == "resume.pdf"


def test_sanitize_replaces_unsafe_characters() -> None:
    result = sanitize_original_filename('resume<>:"|?.pdf')
    assert not any(char in result for char in '<>:"|?')


def test_sanitize_falls_back_when_name_is_empty_after_cleanup() -> None:
    assert sanitize_original_filename("...") == "resume.pdf"


def test_sanitize_preserves_unicode_characters() -> None:
    assert sanitize_original_filename("résumé_日本語.pdf") == "résumé_日本語.pdf"
