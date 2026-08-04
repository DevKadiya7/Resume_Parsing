"""ORM models for the global skill catalog and its per-resume associations."""

import uuid

from sqlalchemy import ForeignKey, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class Skill(Base):
    """A single canonical skill, shared across all resumes.

    Kept as its own table (rather than a free-text column on the resume)
    so the same skill is stored once regardless of how many resumes
    mention it — `ResumeSkill` links resumes to skills many-to-many.
    """

    __tablename__ = "skills"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)


class ResumeSkill(Base):
    """Many-to-many association between a resume and a skill."""

    __tablename__ = "resume_skills"

    resume_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("resumes.id", ondelete="CASCADE"),
        primary_key=True,
    )
    skill_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("skills.id", ondelete="CASCADE"),
        primary_key=True,
    )
