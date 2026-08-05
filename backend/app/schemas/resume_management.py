"""Pydantic v2 schemas for resume listing, search, detail, and statistics."""

import enum
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

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

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "page": 1,
                "page_size": 20,
                "total": 54,
                "items": [
                    {
                        "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                        "filename": "jane_doe_resume.pdf",
                        "status": "UPLOADED",
                        "file_size": 245678,
                        "content_type": "application/pdf",
                        "is_parsed": True,
                        "created_at": "2026-08-05T10:15:30Z",
                        "updated_at": "2026-08-05T10:15:35Z",
                    }
                ],
            }
        }
    )

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
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total_resumes": 120,
                "parsed": 118,
                "pending": 2,
                "top_skills": [{"skill": "Python", "count": 85}],
                "top_companies": [{"company": "Google", "count": 12}],
                "top_colleges": [{"college": "MIT", "count": 9}],
                "most_common_degree": [{"degree": "B.Tech", "count": 40}],
            }
        }
    )

    total_resumes: int
    parsed: int
    pending: int
    top_skills: list[SkillCount] = Field(default_factory=list)
    top_companies: list[CompanyCount] = Field(default_factory=list)
    top_colleges: list[CollegeCount] = Field(default_factory=list)
    most_common_degree: list[DegreeCount] = Field(default_factory=list)
