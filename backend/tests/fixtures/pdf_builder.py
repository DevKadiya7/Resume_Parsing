"""Builds synthetic PDF resumes for tests using PyMuPDF itself.

Avoids depending on real resume samples — content is plain, deterministic
text so extraction results can be asserted precisely.
"""

import fitz  # PyMuPDF

_PAGE_RECT = fitz.Rect(36, 36, 576, 756)


def build_pdf(*pages_text: str) -> bytes:
    """Build a PDF with one page per given string."""
    document = fitz.open()
    try:
        for text in pages_text:
            page = document.new_page(width=612, height=792)
            page.insert_textbox(_PAGE_RECT, text, fontsize=10)
        return document.tobytes()
    finally:
        document.close()


def build_encrypted_pdf(text: str, user_password: str = "secret123") -> bytes:
    """Build a single-page PDF that requires `user_password` to open."""
    document = fitz.open()
    try:
        page = document.new_page(width=612, height=792)
        page.insert_textbox(_PAGE_RECT, text, fontsize=10)
        return document.tobytes(
            encryption=fitz.PDF_ENCRYPT_AES_256,
            owner_pw="owner-" + user_password,
            user_pw=user_password,
        )
    finally:
        document.close()


def build_empty_pdf() -> bytes:
    """Build a single-page PDF with no text content at all."""
    document = fitz.open()
    try:
        document.new_page(width=612, height=792)
        return document.tobytes()
    finally:
        document.close()


CORRUPTED_PDF_BYTES = b"%PDF-1.4\nThis is not a real PDF body, just garbage bytes.\n%%EOF"

FULL_RESUME_TEXT = """John Smith
john.smith@example.com
+1 555-123-4567
linkedin.com/in/johnsmith
github.com/johnsmith

SUMMARY
Experienced software engineer with a passion for backend systems.

SKILLS
Python, FastAPI, PostgreSQL, Docker, AWS, React

EDUCATION
B.Tech in Computer Science
Indian Institute of Technology
Aug 2016 - May 2020
CGPA: 8.7

EXPERIENCE
Software Engineer at Acme Corp
Jan 2021 - Present
Built and maintained backend services for the payments platform.

PROJECTS
Resume Parser
Technologies: Python, spaCy, PyMuPDF
A tool that extracts structured data from PDF resumes.

CERTIFICATIONS
AWS Certified Solutions Architect - Amazon Web Services, 2022
"""

RESUME_WITHOUT_EXPERIENCE_TEXT = """Jane Doe
jane.doe@example.com
+1 555-987-6543

SKILLS
Java, Spring Boot, MySQL

EDUCATION
Master of Science in Data Science
Stanford University
2019 - 2021
"""

RESUME_WITHOUT_EDUCATION_TEXT = """Alex Rivera
alex.rivera@example.com
+1 555-222-3333

SKILLS
Go, Kubernetes, Docker, Terraform

EXPERIENCE
DevOps Engineer at CloudWorks
Mar 2019 - Dec 2022
Automated deployment pipelines and managed cloud infrastructure.
"""

RESUME_PAGE_ONE_TEXT = """Priya Nair
priya.nair@example.com
+91 9876543210

EXPERIENCE
Backend Developer at DataSoft
Jun 2018 - Present
Designed REST APIs for the analytics platform.
"""

RESUME_PAGE_TWO_TEXT = """EDUCATION
B.E. in Information Technology
Anna University
2014 - 2018

CERTIFICATIONS
Certified Kubernetes Administrator - CNCF, 2021
"""
