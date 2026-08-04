"""Pydantic v2 schemas for resume listing, search, detail, and statistics."""

import enum
import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.resume import Resume, ResumeStatus
from app.schemas.parsed_resume import ParsedResumeData


class ResumeSortField(str, enum.Enum):
    CREATED_AT = "created_at"
    FILENAME = "filename"
    STATUS = "status"


class SortOrder(str, enum.Enum):
    ASC = "asc"
    DESC = "desc"


class ResumeSummary(BaseModel):
    """Resume metadata — used both as a list item and as the single-resume response."""

    id: uuid.UUID
    filename: str
    status: ResumeStatus
    file_size: int
    content_type: str
    is_parsed: bool
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_resume(cls, resume: Resume, *, is_parsed: bool) -> "ResumeSummary":
        return cls(
            id=resume.id,
            filename=resume.original_filename,
            status=resume.status,
            file_size=resume.file_size,
            content_type=resume.content_type,
            is_parsed=is_parsed,
            created_at=resume.created_at,
            updated_at=resume.updated_at,
        )


class PaginatedResumeResponse(BaseModel):
    """Response envelope shared by the list and search endpoints."""

    page: int
    page_size: int
    total: int
    items: list[ResumeSummary]


class ResumeFullDetailsResponse(BaseModel):
    """Resume metadata plus its full structured parsed data.

    `parsed` is `None` if the resume hasn't been parsed yet — the resume
    itself still exists and its metadata is still meaningful, so this
    returns 200 with `parsed: null` rather than 404 (unlike
    `GET /resumes/{id}/parsed`, which is specifically about parsed data
    and 404s when there is none).
    """

    resume: ResumeSummary
    parsed: ParsedResumeData | None = None


class SkillCount(BaseModel):
    skill: str
    count: int


class CompanyCount(BaseModel):
    company: str
    count: int


class CollegeCount(BaseModel):
    college: str
    count: int


class DegreeCount(BaseModel):
    degree: str
    count: int


class StatisticsResponse(BaseModel):
    total_resumes: int
    parsed: int
    pending: int
    top_skills: list[SkillCount] = Field(default_factory=list)
    top_companies: list[CompanyCount] = Field(default_factory=list)
    top_colleges: list[CollegeCount] = Field(default_factory=list)
    most_common_degree: list[DegreeCount] = Field(default_factory=list)
