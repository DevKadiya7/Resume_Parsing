"""Small, pure filesystem helpers shared by the service layer and app startup."""

import os
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path

# Anything that isn't safe in a filename across common filesystems, plus
# control characters (which could otherwise smuggle a header-injection-style
# payload into a Content-Disposition header built from this name).
_UNSAFE_FILENAME_CHARS = re.compile(r'[\\/:*?"<>|\x00-\x1f]')


def ensure_directory_exists(directory: str | Path) -> None:
    """Create `directory` (and parents) if it does not already exist."""
    os.makedirs(directory, exist_ok=True)


def generate_stored_filename(extension: str = ".pdf") -> str:
    """Generate a collision-safe, UUID-based filename for disk storage."""
    return f"{uuid.uuid4()}{extension}"


_WINDOWS_DRIVE_PATH = re.compile(r"^[A-Za-z]:[\\/]")


def is_dangerous_filename(filename: str) -> bool:
    """Whether `filename` should be rejected outright rather than merely sanitized.

    Covers null bytes, explicit path-traversal sequences, and absolute
    paths — signs of a deliberate attempt to escape the upload directory,
    as opposed to an ordinary filename that just needs light cleanup (see
    `sanitize_original_filename`). Checked with explicit string patterns
    rather than `Path.is_absolute()`, which is platform-dependent (e.g.
    `Path("/etc/passwd").is_absolute()` is `False` on Windows) and would
    let an absolute POSIX path in a client-supplied filename slip through
    when the server happens to be running on Windows.
    """
    if "\x00" in filename:
        return True
    if ".." in filename:
        return True
    if filename.startswith(("/", "\\")):
        return True
    return bool(_WINDOWS_DRIVE_PATH.match(filename))


def sanitize_original_filename(filename: str) -> str:
    """Reduce a client-supplied filename to a safe *display* name.

    Strips any directory components — defending against path traversal via
    `"../"` or an absolute path smuggled into the `filename` part of a
    multipart upload — and control/reserved characters. This sanitized
    name is only ever used for display (`original_filename` in API
    responses, the download `Content-Disposition` header): the file itself
    is always stored on disk under a generated UUID name (see
    `generate_stored_filename`), so this function never influences where
    anything is written.
    """
    basename = Path(filename).name  # drops any leading directory components
    cleaned = _UNSAFE_FILENAME_CHARS.sub("_", basename).strip().strip(".")
    return cleaned or "resume.pdf"


def build_storage_path(
    upload_directory: str, stored_filename: str, *, when: datetime | None = None
) -> Path:
    """Resolve the on-disk path for a stored file.

    Files are partitioned by upload date — `<upload_directory>/<year>/<month>/<stored_filename>`
    — so a single directory never accumulates an unbounded number of
    entries as the corpus grows, which matters for filesystem/backup
    tooling that degrades with very large directories.
    """
    moment = when or datetime.now(timezone.utc)
    return Path(upload_directory) / f"{moment.year:04d}" / f"{moment.month:02d}" / stored_filename
