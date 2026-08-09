"""FastAPI dependency providers wiring the layers together.

Kept separate from the route modules so the DI graph (session ->
repository -> service) is defined in one obvious place.
"""

import threading
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.db.database import get_db
from app.repositories.parsed_resume_repository import ParsedResumeRepository
from app.repositories.resume_repository import ResumeRepository
from app.services.ml_model_service import MLModelService
from app.services.parser_service import ParserService
from app.services.resume_classification_service import ResumeClassificationService
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
    parsed_resume_repository: Annotated[
        ParsedResumeRepository, Depends(get_parsed_resume_repository)
    ],
    parser_service: Annotated[ParserService, Depends(get_parser_service)],
) -> ResumeParsingService:
    return ResumeParsingService(
        resume_repository=resume_repository,
        parsed_resume_repository=parsed_resume_repository,
        parser_service=parser_service,
    )


def get_resume_management_service(
    resume_repository: Annotated[ResumeRepository, Depends(get_resume_repository)],
    parsed_resume_repository: Annotated[
        ParsedResumeRepository, Depends(get_parsed_resume_repository)
    ],
) -> ResumeManagementService:
    return ResumeManagementService(
        resume_repository=resume_repository,
        parsed_resume_repository=parsed_resume_repository,
    )


# The classification model is process-wide state, unlike every other service
# here, which is cheap to rebuild per request. `MLModelService` caches ~2.7 MB
# of unpickled artifacts internally, so a fresh instance per request would
# reload them every time and defeat the point of lazy caching. One instance is
# therefore held for the process lifetime; constructing it does no I/O, and the
# artifacts load on the first prediction.
_ml_model_service: MLModelService | None = None
_ml_model_service_lock = threading.Lock()


def get_ml_model_service(
    settings: Annotated[Settings, Depends(get_settings)],
) -> MLModelService:
    """Return the process-wide model service, creating it on first use."""
    global _ml_model_service

    if _ml_model_service is None:
        with _ml_model_service_lock:
            if _ml_model_service is None:
                _ml_model_service = MLModelService(
                    artifacts_directory=settings.ML_ARTIFACTS_DIRECTORY,
                    strict_version_check=settings.ML_STRICT_VERSION_CHECK,
                )
    return _ml_model_service


def reset_ml_model_service() -> None:
    """Drop the cached model service. Test-support only.

    Tests need to point the service at different artifact directories
    (missing, corrupted, valid) within one process; without this the first
    test's instance would be reused by all the others.
    """
    global _ml_model_service
    with _ml_model_service_lock:
        _ml_model_service = None


def get_resume_classification_service(
    resume_repository: Annotated[ResumeRepository, Depends(get_resume_repository)],
    ml_model_service: Annotated[MLModelService, Depends(get_ml_model_service)],
) -> ResumeClassificationService:
    return ResumeClassificationService(
        resume_repository=resume_repository,
        ml_model_service=ml_model_service,
    )
