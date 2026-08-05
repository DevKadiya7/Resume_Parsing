"""ORM model for uploaded resumes."""

import enum
import uuid
from datetime import datetime

from sqlalchemy import BigInteger, DateTime
from sqlalchemy import Enum as SAEnum
from sqlalchemy import String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class ResumeStatus(str, enum.Enum):
    """Lifecycle status of an uploaded resume.

    Phase 1 only ever writes UPLOADED (on success) or FAILED (on a
    storage/persistence error). Parsing-related statuses are intentionally
    out of scope until Phase 2.
    """

    UPLOADED = "UPLOADED"
    FAILED = "FAILED"


class Resume(Base):
    """A resume file uploaded by a user, along with its storage metadata."""

    __tablename__ = "resumes"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    stored_filename: Mapped[str] = mapped_column(
        String(255), nullable=False, unique=True, index=True
    )
    storage_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    file_size: Mapped[int] = mapped_column(BigInteger, nullable=False)
    content_type: Mapped[str] = mapped_column(String(127), nullable=False)
    status: Mapped[ResumeStatus] = mapped_column(
        SAEnum(ResumeStatus, name="resume_status"),
        nullable=False,
        default=ResumeStatus.UPLOADED,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
