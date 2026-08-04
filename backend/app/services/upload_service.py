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
from app.utils.file_utils import build_storage_path, generate_stored_filename

logger = get_logger(__name__)

_PDF_CONTENT_TYPE = "application/pdf"
_PDF_EXTENSION = ".pdf"


class UploadService:
    """Coordinates validation, disk storage, and metadata persistence for uploads."""

    def __init__(self, repository: ResumeRepository, settings: Settings) -> None:
        self._repository = repository
        self._settings = settings

    async def upload_resume(self, file: UploadFile) -> Resume:
        content = await self._read_and_validate(file)

        stored_filename = generate_stored_filename(_PDF_EXTENSION)
        storage_path = build_storage_path(self._settings.UPLOAD_DIRECTORY, stored_filename)

        await self._write_to_disk(storage_path, content)

        resume = Resume(
            original_filename=file.filename,
            stored_filename=stored_filename,
            storage_path=str(storage_path),
            file_size=len(content),
            content_type=file.content_type or _PDF_CONTENT_TYPE,
            status=ResumeStatus.UPLOADED,
        )

        try:
            resume = await self._repository.create(resume)
        except Exception:
            logger.exception("Failed to persist resume metadata for %s", file.filename)
            self._delete_file(storage_path)
            raise StorageException("Failed to save resume metadata.") from None

        logger.info("Upload success: id=%s filename=%s", resume.id, resume.original_filename)
        return resume

    async def _read_and_validate(self, file: UploadFile) -> bytes:
        if file is None or not file.filename:
            raise MissingFileException("A file is required.")

        is_pdf_extension = file.filename.lower().endswith(_PDF_EXTENSION)
        is_pdf_content_type = file.content_type == _PDF_CONTENT_TYPE
        if not (is_pdf_extension and is_pdf_content_type):
            logger.warning(
                "Upload rejected — invalid file type: filename=%s content_type=%s",
                file.filename,
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
                file.filename,
                len(content),
            )
            raise FileTooLargeException(f"File size exceeds the {max_mb}MB limit.")

        return content

    @staticmethod
    async def _write_to_disk(path: Path, content: bytes) -> None:
        try:
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
