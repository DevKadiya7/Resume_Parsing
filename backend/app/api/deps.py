"""FastAPI dependency providers wiring the layers together.

Kept separate from the route modules so the DI graph (session ->
repository -> service) is defined in one obvious place.
"""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.db.database import get_db
from app.repositories.parsed_resume_repository import ParsedResumeRepository
from app.repositories.resume_repository import ResumeRepository
from app.services.parser_service import ParserService
from app.services.resume_management_service import ResumeManagementService
from app.services.resume_parsing_service import ResumeParsingService
from app.services.upload_service import UploadService


def get_resume_repository(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ResumeRepository:
    return ResumeRepository(db)


def get_parsed_resume_repository(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ParsedResumeRepository:
    return ParsedResumeRepository(db)


def get_upload_service(
    repository: Annotated[ResumeRepository, Depends(get_resume_repository)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> UploadService:
    return UploadService(repository=repository, settings=settings)


def get_parser_service() -> ParserService:
    return ParserService()


def get_resume_parsing_service(
    resume_repository: Annotated[ResumeRepository, Depends(get_resume_repository)],
    parsed_resume_repository: Annotated[ParsedResumeRepository, Depends(get_parsed_resume_repository)],
    parser_service: Annotated[ParserService, Depends(get_parser_service)],
) -> ResumeParsingService:
    return ResumeParsingService(
        resume_repository=resume_repository,
        parsed_resume_repository=parsed_resume_repository,
        parser_service=parser_service,
    )


def get_resume_management_service(
    resume_repository: Annotated[ResumeRepository, Depends(get_resume_repository)],
    parsed_resume_repository: Annotated[ParsedResumeRepository, Depends(get_parsed_resume_repository)],
) -> ResumeManagementService:
    return ResumeManagementService(
        resume_repository=resume_repository,
        parsed_resume_repository=parsed_resume_repository,
    )
