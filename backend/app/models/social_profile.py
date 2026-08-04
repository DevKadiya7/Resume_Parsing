"""ORM model for social/portfolio links extracted from a resume."""

import enum
import uuid

from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKey, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class SocialPlatform(str, enum.Enum):
    LINKEDIN = "LINKEDIN"
    GITHUB = "GITHUB"
    TWITTER = "TWITTER"
    MEDIUM = "MEDIUM"
    PORTFOLIO = "PORTFOLIO"


class SocialProfile(Base):
    """A single social/portfolio link belonging to a resume."""

    __tablename__ = "social_profiles"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    resume_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("resumes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    platform: Mapped[SocialPlatform] = mapped_column(
        SAEnum(SocialPlatform, name="social_platform"), nullable=False
    )
    url: Mapped[str] = mapped_column(String(1024), nullable=False)
