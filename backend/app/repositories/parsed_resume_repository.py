"""Data-access layer for a resume's parsed data.

Treated as a single repository — rather than one per table — because
`PersonalInfo`, `SocialProfile`, `Education`, `Experience`, `Skill`/
`ResumeSkill`, `Certification`, and `Project` together form one
persistence unit for a given resume: they are always written together
(one parse = one transaction) and always read together (one
`GET .../parsed` = one fetch).
"""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.certification import Certification
from app.models.education import Education
from app.models.experience import Experience
from app.models.personal_info import PersonalInfo
from app.models.project import Project
from app.models.skill import ResumeSkill, Skill
from app.models.social_profile import SocialProfile
from app.schemas.parsed_resume import (
    CertificationSchema,
    EducationSchema,
    ExperienceSchema,
    ParsedResumeData,
    PersonalInfoSchema,
    ProjectSchema,
    SocialProfileSchema,
)


class ParsedResumeRepository:
    """Persistence operations for a resume's parsed-data aggregate."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def exists_for_resume(self, resume_id: uuid.UUID) -> bool:
        """Whether `resume_id` has already been parsed (used for duplicate-parse detection)."""
        result = await self._db.execute(
            select(PersonalInfo.id).where(PersonalInfo.resume_id == resume_id)
        )
        return result.scalar_one_or_none() is not None

    async def save_parsed_data(self, resume_id: uuid.UUID, data: ParsedResumeData) -> None:
        """Persist every extracted entity for `resume_id` in a single transaction.

        Any failure rolls back the entire set, so a resume never ends up
        with partially-saved parsed data. Each entity list is inserted with
        one `add_all()` (a single batched INSERT) rather than one `add()`
        call per row, and per-resume skills are resolved against the global
        catalog with one bulk lookup query instead of one query per skill.
        """
        try:
            self._db.add(PersonalInfo(resume_id=resume_id, **data.personal_info.model_dump()))

            self._db.add_all(
                Education(resume_id=resume_id, **education.model_dump())
                for education in data.education
            )
            self._db.add_all(
                Experience(resume_id=resume_id, **experience.model_dump())
                for experience in data.experience
            )
            self._db.add_all(
                Project(resume_id=resume_id, **project.model_dump()) for project in data.projects
            )
            self._db.add_all(
                Certification(resume_id=resume_id, **certification.model_dump())
                for certification in data.certifications
            )
            self._db.add_all(
                SocialProfile(resume_id=resume_id, **social_profile.model_dump())
                for social_profile in data.social_profiles
            )

            skill_ids = await self._resolve_skill_ids(data.skills)
            self._db.add_all(
                ResumeSkill(resume_id=resume_id, skill_id=skill_id) for skill_id in skill_ids
            )

            await self._db.commit()
        except Exception:
            await self._db.rollback()
            raise

    async def _resolve_skill_ids(self, skill_names: list[str]) -> list[uuid.UUID]:
        """Map skill names to `Skill.id`s, creating any that don't exist yet.

        One `SELECT ... WHERE name IN (...)` resolves every already-known
        skill at once, and only genuinely new names are inserted (also in
        one batch) — a single resume's worth of skills no longer costs one
        query per skill against the global catalog.
        """
        unique_names = sorted(set(skill_names))
        if not unique_names:
            return []

        existing = (
            await self._db.scalars(select(Skill).where(Skill.name.in_(unique_names)))
        ).all()
        skill_id_by_name = {skill.name: skill.id for skill in existing}

        missing_names = [name for name in unique_names if name not in skill_id_by_name]
        if missing_names:
            new_skills = [Skill(name=name) for name in missing_names]
            self._db.add_all(new_skills)
            await self._db.flush()  # assign IDs without committing yet
            skill_id_by_name.update({skill.name: skill.id for skill in new_skills})

        return [skill_id_by_name[name] for name in unique_names]

    async def get_by_resume_id(self, resume_id: uuid.UUID) -> ParsedResumeData | None:
        """Fetch and reassemble the full parsed-data aggregate for a resume.

        Returns `None` if the resume has no parsed data yet.
        """
        personal_info = await self._db.scalar(
            select(PersonalInfo).where(PersonalInfo.resume_id == resume_id)
        )
        if personal_info is None:
            return None

        education = (
            await self._db.scalars(select(Education).where(Education.resume_id == resume_id))
        ).all()
        experience = (
            await self._db.scalars(select(Experience).where(Experience.resume_id == resume_id))
        ).all()
        projects = (
            await self._db.scalars(select(Project).where(Project.resume_id == resume_id))
        ).all()
        certifications = (
            await self._db.scalars(
                select(Certification).where(Certification.resume_id == resume_id)
            )
        ).all()
        social_profiles = (
            await self._db.scalars(
                select(SocialProfile).where(SocialProfile.resume_id == resume_id)
            )
        ).all()
        skill_names = (
            await self._db.scalars(
                select(Skill.name)
                .join(ResumeSkill, ResumeSkill.skill_id == Skill.id)
                .where(ResumeSkill.resume_id == resume_id)
            )
        ).all()

        return ParsedResumeData(
            personal_info=PersonalInfoSchema.model_validate(personal_info),
            skills=sorted(skill_names),
            education=[EducationSchema.model_validate(row) for row in education],
            experience=[ExperienceSchema.model_validate(row) for row in experience],
            projects=[ProjectSchema.model_validate(row) for row in projects],
            certifications=[CertificationSchema.model_validate(row) for row in certifications],
            social_profiles=[SocialProfileSchema.model_validate(row) for row in social_profiles],
        )
