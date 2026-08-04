"""Data-access layer for the `Resume` model.

The repository is the only layer allowed to talk to the SQLAlchemy
session directly. Services depend on this abstraction rather than the
session, which keeps persistence concerns out of business logic and
makes the service layer trivially testable with a fake repository.
"""

import uuid
from datetime import date

from sqlalchemy import and_, delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.certification import Certification
from app.models.education import Education
from app.models.experience import Experience
from app.models.personal_info import PersonalInfo
from app.models.project import Project
from app.models.resume import Resume
from app.models.skill import ResumeSkill, Skill
from app.models.social_profile import SocialPlatform, SocialProfile
from app.schemas.resume_management import (
    CollegeCount,
    CompanyCount,
    DegreeCount,
    ResumeSortField,
    SkillCount,
    SortOrder,
    StatisticsResponse,
)
from app.schemas.resume_query import ResumeListCriteria, ResumeSearchCriteria
from app.utils.experience_calculator import calculate_total_experience_years

_SORT_COLUMNS = {
    ResumeSortField.CREATED_AT: Resume.created_at,
    ResumeSortField.FILENAME: Resume.original_filename,
    ResumeSortField.STATUS: Resume.status,
}


class ResumeRepository:
    """Persistence operations for `Resume` records."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def create(self, resume: Resume) -> Resume:
        """Persist a new resume record and return it with DB-generated fields populated."""
        self._db.add(resume)
        await self._db.commit()
        await self._db.refresh(resume)
        return resume

    async def get_by_id(self, resume_id: uuid.UUID) -> Resume | None:
        """Fetch a resume by primary key, or `None` if it doesn't exist."""
        return await self._db.get(Resume, resume_id)

    async def delete_resume(self, resume_id: uuid.UUID) -> bool:
        """Delete a resume row. Child rows cascade via `ON DELETE CASCADE`.

        Returns whether a row was actually deleted.
        """
        result = await self._db.execute(delete(Resume).where(Resume.id == resume_id))
        await self._db.commit()
        return result.rowcount > 0

    # -- Listing -----------------------------------------------------------

    async def find_all(
        self, criteria: ResumeListCriteria
    ) -> tuple[list[tuple[Resume, bool]], int]:
        """Paginated, sorted, filtered resume listing.

        Returns `(rows, total)` where each row is `(Resume, is_parsed)` —
        `is_parsed` is computed in the same query (a correlated `EXISTS`
        against `personal_info`) rather than with a follow-up query per
        resume, avoiding N+1.
        """
        conditions = self._build_list_conditions(criteria)

        if criteria.minimum_experience is not None:
            return await self._find_all_with_minimum_experience(criteria, conditions)

        return await self._paginated_query(
            conditions, criteria.page, criteria.page_size, criteria.sort, criteria.order
        )

    def _build_list_conditions(self, criteria: ResumeListCriteria) -> list:
        conditions = []

        if criteria.uploaded_after is not None:
            conditions.append(Resume.created_at >= criteria.uploaded_after)
        if criteria.uploaded_before is not None:
            conditions.append(Resume.created_at <= criteria.uploaded_before)
        if criteria.parsed is not None:
            is_parsed = self._is_parsed_expr()
            conditions.append(is_parsed if criteria.parsed else ~is_parsed)
        if criteria.has_projects is not None:
            has_projects = select(Project.id).where(Project.resume_id == Resume.id).exists()
            conditions.append(has_projects if criteria.has_projects else ~has_projects)
        if criteria.has_certifications is not None:
            has_certs = (
                select(Certification.id).where(Certification.resume_id == Resume.id).exists()
            )
            conditions.append(has_certs if criteria.has_certifications else ~has_certs)
        if criteria.has_experience is not None:
            has_exp = select(Experience.id).where(Experience.resume_id == Resume.id).exists()
            conditions.append(has_exp if criteria.has_experience else ~has_exp)

        return conditions

    async def _find_all_with_minimum_experience(
        self, criteria: ResumeListCriteria, conditions: list
    ) -> tuple[list[tuple[Resume, bool]], int]:
        """Handle `minimum_experience` filtering.

        Total years of experience is a derived value (sum of date-range
        durations) that isn't portable to express as a single SQL
        expression across Postgres and SQLite without dialect-specific
        date arithmetic. Instead: apply every other filter in SQL to get a
        candidate ID set, compute total experience for just that set in
        Python, then apply the final filter/sort/paginate over the
        (typically much smaller) qualifying set.
        """
        id_stmt = select(Resume.id)
        if conditions:
            id_stmt = id_stmt.where(and_(*conditions))
        candidate_ids = list((await self._db.execute(id_stmt)).scalars().all())

        if not candidate_ids:
            return [], 0

        exp_stmt = select(
            Experience.resume_id, Experience.start_date, Experience.end_date
        ).where(Experience.resume_id.in_(candidate_ids))
        exp_rows = (await self._db.execute(exp_stmt)).all()

        entries_by_resume: dict[uuid.UUID, list[tuple[date | None, date | None]]] = {}
        for resume_id, start_date, end_date in exp_rows:
            entries_by_resume.setdefault(resume_id, []).append((start_date, end_date))

        qualifying_ids = [
            resume_id
            for resume_id in candidate_ids
            if calculate_total_experience_years(entries_by_resume.get(resume_id, []))
            >= criteria.minimum_experience
        ]

        total = len(qualifying_ids)
        if not qualifying_ids:
            return [], 0

        order_clause = self._order_clause(criteria.sort, criteria.order)
        stmt = (
            select(Resume, self._is_parsed_expr().label("is_parsed"))
            .where(Resume.id.in_(qualifying_ids))
            .order_by(order_clause)
            .offset((criteria.page - 1) * criteria.page_size)
            .limit(criteria.page_size)
        )
        rows = (await self._db.execute(stmt)).all()
        return [(resume, is_parsed) for resume, is_parsed in rows], total

    # -- Search --------------------------------------------------------------

    async def search(
        self, criteria: ResumeSearchCriteria
    ) -> tuple[list[tuple[Resume, bool]], int]:
        """Multi-field, partial, case-insensitive search across a resume's
        parsed data. Every provided field narrows the result set (AND).
        """
        conditions = []

        if criteria.name:
            conditions.append(
                select(PersonalInfo.id)
                .where(
                    PersonalInfo.resume_id == Resume.id,
                    PersonalInfo.full_name.ilike(f"%{criteria.name}%"),
                )
                .exists()
            )
        if criteria.email:
            conditions.append(
                select(PersonalInfo.id)
                .where(
                    PersonalInfo.resume_id == Resume.id,
                    PersonalInfo.email.ilike(f"%{criteria.email}%"),
                )
                .exists()
            )
        if criteria.phone:
            conditions.append(
                select(PersonalInfo.id)
                .where(
                    PersonalInfo.resume_id == Resume.id,
                    PersonalInfo.phone.ilike(f"%{criteria.phone}%"),
                )
                .exists()
            )
        if criteria.skill:
            conditions.append(
                select(ResumeSkill.resume_id)
                .join(Skill, Skill.id == ResumeSkill.skill_id)
                .where(ResumeSkill.resume_id == Resume.id, Skill.name.ilike(f"%{criteria.skill}%"))
                .exists()
            )
        if criteria.college:
            conditions.append(
                select(Education.id)
                .where(
                    Education.resume_id == Resume.id,
                    Education.institution.ilike(f"%{criteria.college}%"),
                )
                .exists()
            )
        if criteria.degree:
            conditions.append(
                select(Education.id)
                .where(
                    Education.resume_id == Resume.id,
                    Education.degree.ilike(f"%{criteria.degree}%"),
                )
                .exists()
            )
        if criteria.company:
            conditions.append(
                select(Experience.id)
                .where(
                    Experience.resume_id == Resume.id,
                    Experience.company.ilike(f"%{criteria.company}%"),
                )
                .exists()
            )
        if criteria.job_title:
            conditions.append(
                select(Experience.id)
                .where(
                    Experience.resume_id == Resume.id,
                    Experience.job_title.ilike(f"%{criteria.job_title}%"),
                )
                .exists()
            )
        if criteria.certification:
            conditions.append(
                select(Certification.id)
                .where(
                    Certification.resume_id == Resume.id,
                    Certification.name.ilike(f"%{criteria.certification}%"),
                )
                .exists()
            )
        if criteria.github:
            conditions.append(self._social_profile_condition(SocialPlatform.GITHUB, criteria.github))
        if criteria.linkedin:
            conditions.append(
                self._social_profile_condition(SocialPlatform.LINKEDIN, criteria.linkedin)
            )
        if criteria.portfolio:
            conditions.append(
                self._social_profile_condition(SocialPlatform.PORTFOLIO, criteria.portfolio)
            )

        return await self._paginated_query(
            conditions, criteria.page, criteria.page_size, criteria.sort, criteria.order
        )

    @staticmethod
    def _social_profile_condition(platform: SocialPlatform, value: str):
        return (
            select(SocialProfile.id)
            .where(
                SocialProfile.resume_id == Resume.id,
                SocialProfile.platform == platform,
                SocialProfile.url.ilike(f"%{value}%"),
            )
            .exists()
        )

    # -- Convenience single-field finders (explicit per spec) ----------------

    async def find_by_name(self, name: str) -> list[Resume]:
        stmt = select(Resume).where(
            select(PersonalInfo.id)
            .where(PersonalInfo.resume_id == Resume.id, PersonalInfo.full_name.ilike(f"%{name}%"))
            .exists()
        )
        return list((await self._db.scalars(stmt)).all())

    async def find_by_skill(self, skill: str) -> list[Resume]:
        stmt = select(Resume).where(
            select(ResumeSkill.resume_id)
            .join(Skill, Skill.id == ResumeSkill.skill_id)
            .where(ResumeSkill.resume_id == Resume.id, Skill.name.ilike(f"%{skill}%"))
            .exists()
        )
        return list((await self._db.scalars(stmt)).all())

    async def find_by_company(self, company: str) -> list[Resume]:
        stmt = select(Resume).where(
            select(Experience.id)
            .where(Experience.resume_id == Resume.id, Experience.company.ilike(f"%{company}%"))
            .exists()
        )
        return list((await self._db.scalars(stmt)).all())

    # -- Statistics ------------------------------------------------------------

    async def statistics(self, top_n: int = 10) -> StatisticsResponse:
        total_resumes = (await self._db.execute(select(func.count(Resume.id)))).scalar_one()
        parsed = (await self._db.execute(select(func.count(PersonalInfo.id)))).scalar_one()

        top_skills_stmt = (
            select(Skill.name, func.count(ResumeSkill.resume_id).label("count"))
            .join(ResumeSkill, ResumeSkill.skill_id == Skill.id)
            .group_by(Skill.name)
            .order_by(func.count(ResumeSkill.resume_id).desc())
            .limit(top_n)
        )
        top_companies_stmt = (
            select(Experience.company, func.count(Experience.id).label("count"))
            .where(Experience.company.is_not(None))
            .group_by(Experience.company)
            .order_by(func.count(Experience.id).desc())
            .limit(top_n)
        )
        top_colleges_stmt = (
            select(Education.institution, func.count(Education.id).label("count"))
            .where(Education.institution.is_not(None))
            .group_by(Education.institution)
            .order_by(func.count(Education.id).desc())
            .limit(top_n)
        )
        top_degrees_stmt = (
            select(Education.degree, func.count(Education.id).label("count"))
            .where(Education.degree.is_not(None))
            .group_by(Education.degree)
            .order_by(func.count(Education.id).desc())
            .limit(top_n)
        )

        top_skills = (await self._db.execute(top_skills_stmt)).all()
        top_companies = (await self._db.execute(top_companies_stmt)).all()
        top_colleges = (await self._db.execute(top_colleges_stmt)).all()
        top_degrees = (await self._db.execute(top_degrees_stmt)).all()

        return StatisticsResponse(
            total_resumes=total_resumes,
            parsed=parsed,
            pending=total_resumes - parsed,
            top_skills=[SkillCount(skill=name, count=count) for name, count in top_skills],
            top_companies=[
                CompanyCount(company=company, count=count) for company, count in top_companies
            ],
            top_colleges=[
                CollegeCount(college=institution, count=count)
                for institution, count in top_colleges
            ],
            most_common_degree=[
                DegreeCount(degree=degree, count=count) for degree, count in top_degrees
            ],
        )

    # -- Shared helpers --------------------------------------------------------

    @staticmethod
    def _is_parsed_expr():
        return select(PersonalInfo.id).where(PersonalInfo.resume_id == Resume.id).exists()

    @staticmethod
    def _order_clause(sort: ResumeSortField, order: SortOrder):
        column = _SORT_COLUMNS[sort]
        return column.desc() if order == SortOrder.DESC else column.asc()

    async def _paginated_query(
        self,
        conditions: list,
        page: int,
        page_size: int,
        sort: ResumeSortField,
        order: SortOrder,
    ) -> tuple[list[tuple[Resume, bool]], int]:
        count_stmt = select(func.count(Resume.id))
        if conditions:
            count_stmt = count_stmt.where(and_(*conditions))
        total = (await self._db.execute(count_stmt)).scalar_one()

        stmt = select(Resume, self._is_parsed_expr().label("is_parsed"))
        if conditions:
            stmt = stmt.where(and_(*conditions))
        stmt = (
            stmt.order_by(self._order_clause(sort, order))
            .offset((page - 1) * page_size)
            .limit(page_size)
        )

        rows = (await self._db.execute(stmt)).all()
        return [(resume, is_parsed) for resume, is_parsed in rows], total
