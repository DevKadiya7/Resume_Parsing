"""Pure resume-parsing orchestration: PDF bytes in, structured data out.

No database or filesystem access happens here — see
`app.services.resume_parsing_service.ResumeParsingService` for the
use-case orchestration (fetching the resume, checking for a duplicate
parse, and persisting the result).
"""

from app.core.logger import get_logger
from app.schemas.parsed_resume import (
    CertificationSchema,
    EducationSchema,
    ExperienceSchema,
    ParsedResumeData,
    PersonalInfoSchema,
    ProjectSchema,
    SocialProfileSchema,
)
from app.services.extractors import (
    certification_extractor,
    contact_extractor,
    education_extractor,
    experience_extractor,
    project_extractor,
    section_splitter,
    skill_extractor,
    social_extractor,
    text_extractor,
)

logger = get_logger(__name__)


class ParserService:
    """Extracts structured resume data from raw PDF bytes.

    Responsibilities, in order: load the PDF and extract its text, clean
    it, split it into named sections, then run one extractor per entity
    type against the relevant section(s).
    """

    def parse(self, pdf_bytes: bytes) -> ParsedResumeData:
        text = text_extractor.extract_text(pdf_bytes)
        logger.info("Text extracted: %d characters", len(text))

        sections = section_splitter.split_sections(text)
        logger.info("Sections identified: %s", sorted(sections.keys()))

        return ParsedResumeData(
            personal_info=self._extract_personal_info(text, sections),
            skills=skill_extractor.extract_skills(sections.get("skills") or text),
            education=[
                EducationSchema(**entry)
                for entry in education_extractor.extract_education(sections.get("education", ""))
            ],
            experience=[
                ExperienceSchema(**entry)
                for entry in experience_extractor.extract_experience(
                    sections.get("experience", "")
                )
            ],
            projects=[
                ProjectSchema(**entry)
                for entry in project_extractor.extract_projects(sections.get("projects", ""))
            ],
            certifications=[
                CertificationSchema(**entry)
                for entry in certification_extractor.extract_certifications(
                    sections.get("certifications", "")
                )
            ],
            social_profiles=[
                SocialProfileSchema(platform=platform, url=url)
                for platform, url in social_extractor.extract_social_profiles(text)
            ],
        )

    @staticmethod
    def _extract_personal_info(full_text: str, sections: dict[str, str]) -> PersonalInfoSchema:
        header_text = sections.get("header", "")
        # Contact details usually live in the header, but fall back to the
        # full document in case a resume places them elsewhere (e.g. a footer).
        contact_text = header_text if header_text.strip() else full_text

        email = contact_extractor.extract_email(contact_text) or contact_extractor.extract_email(
            full_text
        )
        phone = contact_extractor.extract_phone(contact_text) or contact_extractor.extract_phone(
            full_text
        )

        return PersonalInfoSchema(
            full_name=contact_extractor.extract_name(header_text),
            email=email,
            phone=phone,
            address=contact_extractor.extract_address(header_text),
            summary=sections.get("summary") or None,
        )
