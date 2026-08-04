"""Pydantic v2 schemas for the resume upload API."""

import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.resume import Resume, ResumeStatus


class ResumeUploadResponse(BaseModel):
    """Response body returned after a successful resume upload."""

    id: uuid.UUID
    filename: str
    status: ResumeStatus
    created_at: datetime

    @classmethod
    def from_resume(cls, resume: Resume) -> "ResumeUploadResponse":
        """Build the response explicitly rather than relying on ORM
        attribute-name aliasing, which keeps the mapping obvious and
        decouples the wire field name (`filename`) from the model's
        column name (`original_filename`).
        """
        return cls(
            id=resume.id,
            filename=resume.original_filename,
            status=resume.status,
            created_at=resume.created_at,
        )


class ErrorResponse(BaseModel):
    """Consistent error envelope returned by all failure responses."""

    success: bool = False
    message: str
