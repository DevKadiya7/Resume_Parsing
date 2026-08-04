"""ORM model for a resume's certification entries."""

import datetime
import uuid

from sqlalchemy import Date, ForeignKey, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class Certification(Base):
    """A single certification entry."""

    __tablename__ = "certifications"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    resume_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("resumes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    issuer: Mapped[str | None] = mapped_column(String(255), nullable=True)
    date: Mapped[datetime.date | None] = mapped_column(Date, nullable=True)
