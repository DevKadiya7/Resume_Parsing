"""Internal query-criteria bundles passed from the API layer to the repository.

Plain dataclasses rather than Pydantic models: their fields are already
validated by FastAPI's `Query(...)` constraints at the route boundary before
these are constructed, so a second validation pass isn't needed.
"""

from dataclasses import dataclass
from datetime import datetime

from app.schemas.resume_management import ResumeSortField, SortOrder


@dataclass
class ResumeListCriteria:
    page: int = 1
    page_size: int = 20
    sort: ResumeSortField = ResumeSortField.CREATED_AT
    order: SortOrder = SortOrder.DESC
    uploaded_after: datetime | None = None
    uploaded_before: datetime | None = None
    parsed: bool | None = None
    has_projects: bool | None = None
    has_certifications: bool | None = None
    has_experience: bool | None = None
    minimum_experience: float | None = None


@dataclass
class ResumeSearchCriteria:
    page: int = 1
    page_size: int = 20
    sort: ResumeSortField = ResumeSortField.CREATED_AT
    order: SortOrder = SortOrder.DESC
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    skill: str | None = None
    college: str | None = None
    degree: str | None = None
    company: str | None = None
    job_title: str | None = None
    certification: str | None = None
    github: str | None = None
    linkedin: str | None = None
    portfolio: str | None = None
