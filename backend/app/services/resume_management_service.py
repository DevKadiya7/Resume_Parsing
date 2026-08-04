"""Use-case orchestration for browsing, searching, and managing resumes.

Keeps business logic (404 handling, file cleanup on delete, assembling the
nested details response) out of the API routes, following the same pattern
as `UploadService` and `ResumeParsingService`.
"""

import asyncio
import uuid
from pathlib import Path

from app.core.logger import get_logger
from app.exceptions.custom_exceptions import ResumeFileNotFoundException, ResumeNotFoundException
from app.models.resume import Resume
from app.repositories.parsed_resume_repository import ParsedResumeRepository
from app.repositories.resume_repository import ResumeRepository
from app.schemas.resume_management import (
    PaginatedResumeResponse,
    ResumeFullDetailsResponse,
    ResumeSummary,
    StatisticsResponse,
)
from app.schemas.resume_query import ResumeListCriteria, ResumeSearchCriteria

logger = get_logger(__name__)


class ResumeManagementService:
    """Coordinates listing, search, retrieval, statistics, deletion, and download."""

    def __init__(
        self,
        resume_repository: ResumeRepository,
        parsed_resume_repository: ParsedResumeRepository,
    ) -> None:
        self._resume_repository = resume_repository
        self._parsed_resume_repository = parsed_resume_repository

    async def list_resumes(self, criteria: ResumeListCriteria) -> PaginatedResumeResponse:
        rows, total = await self._resume_repository.find_all(criteria)
        return self._to_paginated_response(rows, total, criteria.page, criteria.page_size)

    async def search_resumes(self, criteria: ResumeSearchCriteria) -> PaginatedResumeResponse:
        rows, total = await self._resume_repository.search(criteria)
        return self._to_paginated_response(rows, total, criteria.page, criteria.page_size)

    async def get_resume(self, resume_id: uuid.UUID) -> ResumeSummary:
        resume = await self._get_resume_or_404(resume_id)
        is_parsed = await self._parsed_resume_repository.exists_for_resume(resume_id)
        return ResumeSummary.from_resume(resume, is_parsed=is_parsed)

    async def get_resume_details(self, resume_id: uuid.UUID) -> ResumeFullDetailsResponse:
        resume = await self._get_resume_or_404(resume_id)
        parsed_data = await self._parsed_resume_repository.get_by_resume_id(resume_id)
        return ResumeFullDetailsResponse(
            resume=ResumeSummary.from_resume(resume, is_parsed=parsed_data is not None),
            parsed=parsed_data,
        )

    async def get_statistics(self) -> StatisticsResponse:
        return await self._resume_repository.statistics()

    async def delete_resume(self, resume_id: uuid.UUID) -> None:
        resume = await self._get_resume_or_404(resume_id)
        await self._delete_file(Path(resume.storage_path))
        await self._resume_repository.delete_resume(resume_id)
        logger.info("Resume deleted: resume_id=%s", resume_id)

    async def get_download_target(self, resume_id: uuid.UUID) -> tuple[Path, str]:
        resume = await self._get_resume_or_404(resume_id)
        path = Path(resume.storage_path)
        if not await asyncio.to_thread(path.is_file):
            raise ResumeFileNotFoundException("The resume file could not be found on disk.")
        return path, resume.original_filename

    async def _get_resume_or_404(self, resume_id: uuid.UUID) -> Resume:
        resume = await self._resume_repository.get_by_id(resume_id)
        if resume is None:
            raise ResumeNotFoundException("Resume not found.")
        return resume

    @staticmethod
    def _to_paginated_response(
        rows: list[tuple[Resume, bool]], total: int, page: int, page_size: int
    ) -> PaginatedResumeResponse:
        items = [
            ResumeSummary.from_resume(resume, is_parsed=is_parsed) for resume, is_parsed in rows
        ]
        return PaginatedResumeResponse(page=page, page_size=page_size, total=total, items=items)

    @staticmethod
    async def _delete_file(path: Path) -> None:
        try:
            await asyncio.to_thread(path.unlink, missing_ok=True)
        except OSError:
            logger.warning("Failed to delete resume file from disk at %s", path)
