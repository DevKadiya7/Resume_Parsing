"""Small, pure filesystem helpers shared by the service layer and app startup."""

import os
import uuid
from pathlib import Path


def ensure_directory_exists(directory: str) -> None:
    """Create `directory` (and parents) if it does not already exist."""
    os.makedirs(directory, exist_ok=True)


def generate_stored_filename(extension: str = ".pdf") -> str:
    """Generate a collision-safe, UUID-based filename for disk storage."""
    return f"{uuid.uuid4()}{extension}"


def build_storage_path(upload_directory: str, stored_filename: str) -> Path:
    """Resolve the full on-disk path for a stored file."""
    return Path(upload_directory) / stored_filename
