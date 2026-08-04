"""ORM model for a resume's project entries."""

import uuid

from sqlalchemy import ForeignKey, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class Project(Base):
    """A single project entry.

    `technologies` is stored as a simple comma-separated string rather
    than a normalized join table — projects list free-form tech tags
    that aren't deduplicated/reused across resumes the way `Skill` is,
    so a normalized table would add relational overhead without a
    corresponding benefit.
    """

    __tablename__ = "projects"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    resume_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("resumes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    technologies: Mapped[str | None] = mapped_column(String(1000), nullable=True)
