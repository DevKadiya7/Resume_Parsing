"""Pydantic v2 schemas for parsed resume data.

These schemas serve three roles at once: `ParserService` returns a
`ParsedResumeData` instance, `ParsedResumeRepository` persists it and
reconstructs it from ORM rows (via `from_attributes`), and the API layer
serializes it directly as the response body. Sharing one type across
these layers avoids maintaining a parallel dataclass hierarchy purely
for internal use.
"""

import datetime
import uuid

from pydantic import BaseModel, ConfigDict, Field

from app.models.social_profile import SocialPlatform


class PersonalInfoSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    full_name: str | None = None
    email: str | None = None
    phone: str | None = None
    address: str | None = None
    summary: str | None = None


class SocialProfileSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    platform: SocialPlatform
    url: str


class EducationSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    institution: str | None = None
    degree: str | None = None
    field_of_study: str | None = None
    start_date: datetime.date | None = None
    end_date: datetime.date | None = None
    grade: str | None = None


class ExperienceSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    company: str | None = None
    job_title: str | None = None
    location: str | None = None
    start_date: datetime.date | None = None
    end_date: datetime.date | None = None
    is_current: bool = False
    description: str | None = None


class CertificationSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str | None = None
    issuer: str | None = None
    date: datetime.date | None = None


class ProjectSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str | None = None
    description: str | None = None
    technologies: str | None = None


class ParsedResumeData(BaseModel):
    """The full structured output of parsing one resume."""

    personal_info: PersonalInfoSchema = Field(default_factory=PersonalInfoSchema)
    skills: list[str] = Field(default_factory=list)
    education: list[EducationSchema] = Field(default_factory=list)
    experience: list[ExperienceSchema] = Field(default_factory=list)
    projects: list[ProjectSchema] = Field(default_factory=list)
    certifications: list[CertificationSchema] = Field(default_factory=list)
    social_profiles: list[SocialProfileSchema] = Field(default_factory=list)


class ParseResumeResponse(BaseModel):
    """Response body for both the parse action and the parsed-data lookup."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "resume_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                "parsed": {
                    "personal_info": {
                        "full_name": "Jane Doe",
                        "email": "jane.doe@example.com",
                        "phone": "+1 555-123-4567",
                        "address": "San Francisco, CA",
                        "summary": "Backend engineer with 6 years of experience.",
                    },
                    "skills": ["Docker", "FastAPI", "Python", "SQL"],
                    "education": [
                        {
                            "institution": "MIT",
                            "degree": "B.Tech",
                            "field_of_study": "Computer Science",
                            "start_date": "2015-08-01",
                            "end_date": "2019-05-01",
                            "grade": "8.7 CGPA",
                        }
                    ],
                    "experience": [
                        {
                            "company": "Google",
                            "job_title": "Software Engineer",
                            "location": "Mountain View, CA",
                            "start_date": "2020-01-01",
                            "end_date": None,
                            "is_current": True,
                            "description": "Building scalable backend systems.",
                        }
                    ],
                    "projects": [
                        {
                            "name": "Resume Parser",
                            "description": "Extracts structured data from PDF resumes.",
                            "technologies": "Python, FastAPI",
                        }
                    ],
                    "certifications": [
                        {
                            "name": "AWS Certified Solutions Architect",
                            "issuer": "Amazon Web Services",
                            "date": "2021-06-01",
                        }
                    ],
                    "social_profiles": [
                        {"platform": "LINKEDIN", "url": "linkedin.com/in/janedoe"}
                    ],
                },
            }
        }
    )

    success: bool = True
    resume_id: uuid.UUID
    parsed: ParsedResumeData
