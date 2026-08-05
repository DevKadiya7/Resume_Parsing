"""Use-case orchestration for parsing an uploaded resume.

Fetches the resume record, guards against duplicate parsing, reads the
stored PDF, delegates extraction to `ParserService`, and persists the
result via `ParsedResumeRepository` — the business logic that keeps the
API route thin.
"""

import asyncio
import uuid
from pathlib import Path

from app.core.logger import get_logger
from app.exceptions.custom_exceptions import (
    DuplicateParseException,
    ParsedDataNotFoundException,
    ResumeNotFoundException,
    StorageException,
)
from app.models.resume import Resume
from app.repositories.parsed_resume_repository import ParsedResumeRepository
from app.repositories.resume_repository import ResumeRepository
from app.schemas.parsed_resume import ParsedResumeData
from app.services.parser_service import ParserService

logger = get_logger(__name__)


class ResumeParsingService:
    """Coordinates fetching, parsing, and persisting a resume's structured data."""

    def __init__(
        self,
        resume_repository: ResumeRepository,
        parsed_resume_repository: ParsedResumeRepository,
        parser_service: ParserService,
    ) -> None:
        self._resume_repository = resume_repository
        self._parsed_resume_repository = parsed_resume_repository
        self._parser_service = parser_service

    async def parse_resume(self, resume_id: uuid.UUID) -> ParsedResumeData:
        resume = await self._get_resume_or_404(resume_id)

        if await self._parsed_resume_repository.exists_for_resume(resume_id):
            raise DuplicateParseException("This resume has already been parsed.")

        logger.info("Parsing started: resume_id=%s", resume_id)
        pdf_bytes = await self._read_pdf_bytes(resume)

        try:
            parsed_data = self._parser_service.parse(pdf_bytes)
        except Exception:
            logger.exception("Parsing failed: resume_id=%s", resume_id)
            raise

        await self._parsed_resume_repository.save_parsed_data(resume_id, parsed_data)
        logger.info("Database saved: resume_id=%s", resume_id)

        logger.info("Parsing completed: resume_id=%s", resume_id)
        return parsed_data

    async def get_parsed_data(self, resume_id: uuid.UUID) -> ParsedResumeData:
        await self._get_resume_or_404(resume_id)

        parsed_data = await self._parsed_resume_repository.get_by_resume_id(resume_id)
        if parsed_data is None:
            raise ParsedDataNotFoundException("This resume has not been parsed yet.")
        return parsed_data

    async def _get_resume_or_404(self, resume_id: uuid.UUID) -> Resume:
        resume = await self._resume_repository.get_by_id(resume_id)
        if resume is None:
            raise ResumeNotFoundException("Resume not found.")
        return resume

    @staticmethod
    async def _read_pdf_bytes(resume: Resume) -> bytes:
        try:
            return await asyncio.to_thread(Path(resume.storage_path).read_bytes)
        except OSError as exc:
            logger.exception("Stored resume file missing on disk: resume_id=%s", resume.id)
            raise StorageException("The stored resume file could not be read from disk.") from exc
