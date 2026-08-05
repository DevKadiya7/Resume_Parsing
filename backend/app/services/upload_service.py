"""Business logic for resume uploads.

Validation, filename generation, disk I/O orchestration, and persistence
all live here — never in the API route. The route is a thin adapter
between HTTP and this service.
"""

import asyncio
from pathlib import Path

from fastapi import UploadFile

from app.core.config import Settings
from app.core.logger import get_logger
from app.exceptions.custom_exceptions import (
    FileTooLargeException,
    InvalidFileTypeException,
    MissingFileException,
    StorageException,
)
from app.models.resume import Resume, ResumeStatus
from app.repositories.resume_repository import ResumeRepository
from app.utils.file_utils import (
    build_storage_path,
    ensure_directory_exists,
    generate_stored_filename,
    is_dangerous_filename,
    sanitize_original_filename,
)

logger = get_logger(__name__)

_PDF_CONTENT_TYPE = "application/pdf"
_PDF_EXTENSION = ".pdf"


class UploadService:
    """Coordinates validation, disk storage, and metadata persistence for uploads."""

    def __init__(self, repository: ResumeRepository, settings: Settings) -> None:
        self._repository = repository
        self._settings = settings

    async def upload_resume(self, file: UploadFile) -> Resume:
        filename, content = await self._read_and_validate(file)

        stored_filename = generate_stored_filename(_PDF_EXTENSION)
        storage_path = build_storage_path(self._settings.UPLOAD_DIRECTORY, stored_filename)

        await self._write_to_disk(storage_path, content)

        resume = Resume(
            original_filename=sanitize_original_filename(filename),
            stored_filename=stored_filename,
            storage_path=str(storage_path),
            file_size=len(content),
            content_type=file.content_type or _PDF_CONTENT_TYPE,
            status=ResumeStatus.UPLOADED,
        )

        try:
            resume = await self._repository.create(resume)
        except Exception:
            logger.exception("Failed to persist resume metadata for %s", filename)
            self._delete_file(storage_path)
            raise StorageException("Failed to save resume metadata.") from None

        logger.info("Upload success: id=%s filename=%s", resume.id, resume.original_filename)
        return resume

    async def _read_and_validate(self, file: UploadFile) -> tuple[str, bytes]:
        # Narrowed into a local variable (rather than re-reading
        # `file.filename` throughout) so its non-optional-ness is visible
        # both to mypy and to the rest of this method.
        filename = file.filename
        if not filename:
            raise MissingFileException("A file is required.")

        if is_dangerous_filename(filename):
            logger.warning("Upload rejected — dangerous filename: %r", filename)
            raise InvalidFileTypeException("Filename is not allowed.")

        is_pdf_extension = filename.lower().endswith(_PDF_EXTENSION)
        is_pdf_content_type = file.content_type == _PDF_CONTENT_TYPE
        if not (is_pdf_extension and is_pdf_content_type):
            logger.warning(
                "Upload rejected — invalid file type: filename=%s content_type=%s",
                filename,
                file.content_type,
            )
            raise InvalidFileTypeException("Only PDF files are allowed.")

        content = await file.read()
        if not content:
            raise MissingFileException("Uploaded file is empty.")

        if len(content) > self._settings.MAX_FILE_SIZE:
            max_mb = self._settings.MAX_FILE_SIZE // (1024 * 1024)
            logger.warning(
                "Upload rejected — file too large: filename=%s size=%d",
                filename,
                len(content),
            )
            raise FileTooLargeException(f"File size exceeds the {max_mb}MB limit.")

        return filename, content

    @staticmethod
    async def _write_to_disk(path: Path, content: bytes) -> None:
        try:
            await asyncio.to_thread(ensure_directory_exists, path.parent)
            await asyncio.to_thread(path.write_bytes, content)
        except OSError as exc:
            logger.exception("Failed to write uploaded file to disk at %s", path)
            raise StorageException("Failed to store the uploaded file.") from exc

    @staticmethod
    def _delete_file(path: Path) -> None:
        try:
            path.unlink(missing_ok=True)
        except OSError:
            logger.exception("Failed to clean up orphaned file at %s", path)
