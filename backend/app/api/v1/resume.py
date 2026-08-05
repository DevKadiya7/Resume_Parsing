"""Resume upload, parsing, and management endpoints.

Route registration order matters here: `/resumes/search` and
`/resumes/statistics` are static paths that must be registered before the
dynamic `/resumes/{resume_id}` route, otherwise FastAPI would match
"search"/"statistics" as a `resume_id` value first and fail UUID
validation instead of reaching the intended handler.
"""

from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, Query, Request, Response, UploadFile, status
from fastapi.responses import FileResponse

from app.api.deps import (
    get_resume_management_service,
    get_resume_parsing_service,
    get_upload_service,
)
from app.core.config import get_settings
from app.core.logger import get_logger
from app.core.rate_limiter import limiter
from app.schemas.parsed_resume import ParseResumeResponse
from app.schemas.resume import ErrorResponse, ResumeUploadResponse
from app.schemas.resume_management import (
    PaginatedResumeResponse,
    ResumeFullDetailsResponse,
    ResumeSortField,
    ResumeSummary,
    SortOrder,
    StatisticsResponse,
)
from app.schemas.resume_query import ResumeListCriteria, ResumeSearchCriteria
from app.services.resume_management_service import ResumeManagementService
from app.services.resume_parsing_service import ResumeParsingService
from app.services.upload_service import UploadService
from app.utils.query_params import ensure_known_query_params

logger = get_logger(__name__)
settings = get_settings()

router = APIRouter(prefix="/resumes", tags=["Resumes"])

_LIST_PARAMS = {
    "page",
    "page_size",
    "sort",
    "order",
    "uploaded_after",
    "uploaded_before",
    "parsed",
    "has_projects",
    "has_certifications",
    "has_experience",
    "minimum_experience",
}
_SEARCH_PARAMS = {
    "page",
    "page_size",
    "sort",
    "order",
    "name",
    "email",
    "phone",
    "skill",
    "college",
    "degree",
    "company",
    "job_title",
    "certification",
    "github",
    "linkedin",
    "portfolio",
}


@router.post(
    "/upload",
    response_model=ResumeUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a resume PDF",
    description=(
        "Accepts a single PDF file (max 10MB), stores it on disk under a "
        "generated UUID filename, and persists its metadata."
    ),
    responses={
        400: {"model": ErrorResponse, "description": "Invalid, missing, or oversized file"},
        422: {"model": ErrorResponse, "description": "Request is missing the file part"},
        500: {"model": ErrorResponse, "description": "Storage or persistence failure"},
    },
)
@limiter.limit(settings.RATE_LIMIT_UPLOAD)
async def upload_resume(
    request: Request,
    response: Response,
    upload_service: Annotated[UploadService, Depends(get_upload_service)],
    file: Annotated[UploadFile, File(description="PDF resume file, max 10MB")],
) -> ResumeUploadResponse:
    logger.info("Upload request received: filename=%s", file.filename)
    resume = await upload_service.upload_resume(file)
    return ResumeUploadResponse.from_resume(resume)


@router.get(
    "",
    response_model=PaginatedResumeResponse,
    status_code=status.HTTP_200_OK,
    summary="List resumes",
    description=(
        "Returns all uploaded resumes with pagination, sorting, and "
        "structural filtering.\n\n"
        "Example: `GET /api/v1/resumes?page=1&page_size=20&sort=created_at&order=desc`"
    ),
    responses={400: {"model": ErrorResponse, "description": "Unknown query parameter"}},
)
async def list_resumes(
    request: Request,
    service: Annotated[ResumeManagementService, Depends(get_resume_management_service)],
    page: Annotated[int, Query(ge=1, description="1-indexed page number")] = 1,
    page_size: Annotated[int, Query(ge=1, le=100, description="Items per page (max 100)")] = 20,
    sort: Annotated[ResumeSortField, Query(description="Field to sort by")] = (
        ResumeSortField.CREATED_AT
    ),
    order: Annotated[SortOrder, Query(description="Sort direction")] = SortOrder.DESC,
    uploaded_after: Annotated[
        datetime | None,
        Query(description="ISO 8601 datetime; only resumes uploaded on/after this"),
    ] = None,
    uploaded_before: Annotated[
        datetime | None,
        Query(description="ISO 8601 datetime; only resumes uploaded on/before this"),
    ] = None,
    parsed: Annotated[
        bool | None, Query(description="Only parsed (true) or unparsed (false)")
    ] = None,
    has_projects: Annotated[bool | None, Query()] = None,
    has_certifications: Annotated[bool | None, Query()] = None,
    has_experience: Annotated[bool | None, Query()] = None,
    minimum_experience: Annotated[
        float | None, Query(ge=0, description="Minimum total years of work experience")
    ] = None,
) -> PaginatedResumeResponse:
    ensure_known_query_params(request, _LIST_PARAMS)
    criteria = ResumeListCriteria(
        page=page,
        page_size=page_size,
        sort=sort,
        order=order,
        uploaded_after=uploaded_after,
        uploaded_before=uploaded_before,
        parsed=parsed,
        has_projects=has_projects,
        has_certifications=has_certifications,
        has_experience=has_experience,
        minimum_experience=minimum_experience,
    )
    return await service.list_resumes(criteria)


@router.get(
    "/search",
    response_model=PaginatedResumeResponse,
    status_code=status.HTTP_200_OK,
    summary="Search resumes",
    description=(
        "Partial, case-insensitive search across a resume's parsed data. "
        "Combine multiple fields to narrow results (all provided fields "
        "must match — AND semantics).\n\n"
        "Examples: `?skill=python`, `?company=google`, `?name=dev`, "
        "`?email=gmail.com`, `?skill=python&company=google`"
    ),
    responses={400: {"model": ErrorResponse, "description": "Unknown query parameter"}},
)
async def search_resumes(
    request: Request,
    service: Annotated[ResumeManagementService, Depends(get_resume_management_service)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    sort: Annotated[ResumeSortField, Query()] = ResumeSortField.CREATED_AT,
    order: Annotated[SortOrder, Query()] = SortOrder.DESC,
    name: Annotated[
        str | None, Query(min_length=1, description="Partial match on full name")
    ] = None,
    email: Annotated[str | None, Query(min_length=1)] = None,
    phone: Annotated[str | None, Query(min_length=1)] = None,
    skill: Annotated[str | None, Query(min_length=1)] = None,
    college: Annotated[str | None, Query(min_length=1, description="Institution name")] = None,
    degree: Annotated[str | None, Query(min_length=1)] = None,
    company: Annotated[str | None, Query(min_length=1)] = None,
    job_title: Annotated[str | None, Query(min_length=1)] = None,
    certification: Annotated[str | None, Query(min_length=1)] = None,
    github: Annotated[str | None, Query(min_length=1)] = None,
    linkedin: Annotated[str | None, Query(min_length=1)] = None,
    portfolio: Annotated[str | None, Query(min_length=1)] = None,
) -> PaginatedResumeResponse:
    ensure_known_query_params(request, _SEARCH_PARAMS)
    criteria = ResumeSearchCriteria(
        page=page,
        page_size=page_size,
        sort=sort,
        order=order,
        name=name,
        email=email,
        phone=phone,
        skill=skill,
        college=college,
        degree=degree,
        company=company,
        job_title=job_title,
        certification=certification,
        github=github,
        linkedin=linkedin,
        portfolio=portfolio,
    )
    return await service.search_resumes(criteria)


@router.get(
    "/statistics",
    response_model=StatisticsResponse,
    status_code=status.HTTP_200_OK,
    summary="Aggregate resume statistics",
    description=(
        "Returns corpus-wide counts: total/parsed/pending resumes, and the "
        "top skills, companies, colleges, and degrees by frequency."
    ),
)
async def get_statistics(
    request: Request,
    service: Annotated[ResumeManagementService, Depends(get_resume_management_service)],
) -> StatisticsResponse:
    ensure_known_query_params(request, set())
    return await service.get_statistics()


@router.post(
    "/{resume_id}/parse",
    response_model=ParseResumeResponse,
    status_code=status.HTTP_200_OK,
    summary="Parse an uploaded resume",
    description=(
        "Extracts structured data — personal info, skills, education, "
        "experience, projects, certifications, and social profiles — from "
        "an already-uploaded PDF using PyMuPDF, regex, spaCy, and "
        "dateparser. No LLM or external AI API is used. Each resume can "
        "only be parsed once; re-parsing returns a 409 conflict."
    ),
    responses={
        404: {"model": ErrorResponse, "description": "Resume not found"},
        409: {"model": ErrorResponse, "description": "Resume has already been parsed"},
        422: {"model": ErrorResponse, "description": "Corrupted, encrypted, or empty PDF"},
        500: {"model": ErrorResponse, "description": "Stored file missing or persistence failure"},
    },
)
@limiter.limit(settings.RATE_LIMIT_PARSE)
async def parse_resume(
    request: Request,
    response: Response,
    resume_id: UUID,
    parsing_service: Annotated[ResumeParsingService, Depends(get_resume_parsing_service)],
) -> ParseResumeResponse:
    logger.info("Parse request received: resume_id=%s", resume_id)
    parsed = await parsing_service.parse_resume(resume_id)
    return ParseResumeResponse(resume_id=resume_id, parsed=parsed)


@router.get(
    "/{resume_id}/parsed",
    response_model=ParseResumeResponse,
    status_code=status.HTTP_200_OK,
    summary="Get a resume's parsed data",
    description="Returns the previously extracted structured data for a resume.",
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Resume not found, or it has not been parsed yet",
        },
    },
)
async def get_parsed_resume(
    resume_id: UUID,
    parsing_service: Annotated[ResumeParsingService, Depends(get_resume_parsing_service)],
) -> ParseResumeResponse:
    parsed = await parsing_service.get_parsed_data(resume_id)
    return ParseResumeResponse(resume_id=resume_id, parsed=parsed)


@router.get(
    "/{resume_id}/details",
    response_model=ResumeFullDetailsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get a resume's full details",
    description=(
        "Returns resume metadata nested alongside its full parsed data "
        "(personal info, education, experience, projects, certifications, "
        "skills, social profiles). `parsed` is `null` if the resume hasn't "
        "been parsed yet."
    ),
    responses={404: {"model": ErrorResponse, "description": "Resume not found"}},
)
async def get_resume_details(
    resume_id: UUID,
    service: Annotated[ResumeManagementService, Depends(get_resume_management_service)],
) -> ResumeFullDetailsResponse:
    return await service.get_resume_details(resume_id)


@router.get(
    "/{resume_id}/download",
    status_code=status.HTTP_200_OK,
    summary="Download a resume's original PDF",
    description="Streams the originally uploaded PDF file back to the client.",
    response_class=FileResponse,
    responses={
        200: {"content": {"application/pdf": {}}},
        404: {"model": ErrorResponse, "description": "Resume not found, or its file is missing"},
    },
)
async def download_resume(
    resume_id: UUID,
    service: Annotated[ResumeManagementService, Depends(get_resume_management_service)],
) -> FileResponse:
    path, original_filename = await service.get_download_target(resume_id)
    return FileResponse(
        path=path,
        media_type="application/pdf",
        filename=original_filename,
    )


@router.get(
    "/{resume_id}",
    response_model=ResumeSummary,
    status_code=status.HTTP_200_OK,
    summary="Get a single resume",
    description="Returns resume metadata: upload info, parse status, and timestamps.",
    responses={404: {"model": ErrorResponse, "description": "Resume not found"}},
)
async def get_resume(
    resume_id: UUID,
    service: Annotated[ResumeManagementService, Depends(get_resume_management_service)],
) -> ResumeSummary:
    return await service.get_resume(resume_id)


@router.delete(
    "/{resume_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a resume",
    description=(
        "Deletes the uploaded PDF from disk and its metadata and parsed "
        "data from the database. Parsed-data deletion is automatic via "
        "`ON DELETE CASCADE` foreign keys."
    ),
    responses={404: {"model": ErrorResponse, "description": "Resume not found"}},
)
async def delete_resume(
    resume_id: UUID,
    service: Annotated[ResumeManagementService, Depends(get_resume_management_service)],
) -> None:
    await service.delete_resume(resume_id)
