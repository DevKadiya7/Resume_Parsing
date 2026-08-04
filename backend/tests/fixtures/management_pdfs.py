"""Resume text fixtures used by the resume-management test suite.

Distinct, deterministic content across skills/companies/colleges/degrees so
sorting, filtering, search, and statistics can be asserted precisely.
"""

ALICE_TEXT = """Alice Johnson
alice.johnson@example.com
+1 555-111-2222
linkedin.com/in/alicejohnson
github.com/alicejohnson

SKILLS
Python, FastAPI, Docker

EDUCATION
B.Tech in Computer Science
MIT
Aug 2015 - May 2019

EXPERIENCE
Software Engineer at Google
Jan 2018 - Present
Building scalable backend systems.

PROJECTS
Resume Parser
Technologies: Python, FastAPI
A tool that extracts structured data from PDF resumes.

CERTIFICATIONS
AWS Certified Solutions Architect - Amazon Web Services, 2021
"""

BOB_TEXT = """Bob Lee
bob.lee@example.com
+1 555-333-4444

SKILLS
Java, Spring Boot

EDUCATION
MBA
Stanford University
2018 - 2020

EXPERIENCE
Product Manager at Amazon
Jun 2018 - Dec 2019
Led product strategy for the logistics platform.
"""

CAROL_TEXT = """Carol White
carol.white@example.com
+1 555-777-8888

SKILLS
Python
"""
