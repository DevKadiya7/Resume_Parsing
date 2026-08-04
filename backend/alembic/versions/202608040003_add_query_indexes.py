"""Add indexes for resume listing, sorting, filtering, and search

Revision ID: 202608040003
Revises: 202608040002
Create Date: 2026-08-04 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "202608040003"
down_revision: Union[str, None] = "202608040002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index(op.f("ix_resumes_original_filename"), "resumes", ["original_filename"])
    op.create_index(op.f("ix_resumes_status"), "resumes", ["status"])
    op.create_index(op.f("ix_resumes_created_at"), "resumes", ["created_at"])

    op.create_index(op.f("ix_experience_company"), "experience", ["company"])
    op.create_index(op.f("ix_experience_job_title"), "experience", ["job_title"])

    op.create_index(op.f("ix_education_institution"), "education", ["institution"])
    op.create_index(op.f("ix_education_degree"), "education", ["degree"])

    op.create_index(op.f("ix_certifications_name"), "certifications", ["name"])

    op.create_index(op.f("ix_personal_info_full_name"), "personal_info", ["full_name"])
    op.create_index(op.f("ix_personal_info_email"), "personal_info", ["email"])


def downgrade() -> None:
    op.drop_index(op.f("ix_personal_info_email"), table_name="personal_info")
    op.drop_index(op.f("ix_personal_info_full_name"), table_name="personal_info")
    op.drop_index(op.f("ix_certifications_name"), table_name="certifications")
    op.drop_index(op.f("ix_education_degree"), table_name="education")
    op.drop_index(op.f("ix_education_institution"), table_name="education")
    op.drop_index(op.f("ix_experience_job_title"), table_name="experience")
    op.drop_index(op.f("ix_experience_company"), table_name="experience")
    op.drop_index(op.f("ix_resumes_created_at"), table_name="resumes")
    op.drop_index(op.f("ix_resumes_status"), table_name="resumes")
    op.drop_index(op.f("ix_resumes_original_filename"), table_name="resumes")
