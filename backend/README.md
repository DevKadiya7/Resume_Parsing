# Resume Parsing Service

A backend service that accepts PDF resumes, stores them, and extracts
structured information from them — personal info, skills, education, work
experience, projects, certifications, and social profiles — using **no LLM
or external AI API**. Extraction is done entirely with PyMuPDF (text),
regex (patterns), spaCy (name NER, optional), and dateparser (dates).

- **Phase 1:** project setup, database integration, file upload, clean architecture.
- **Phase 2:** the parsing engine — `POST /api/v1/resumes/{resume_id}/parse` and `GET /api/v1/resumes/{resume_id}/parsed`.

## Folder Structure

```
backend/
├── app/
│   ├── api/
│   │   ├── deps.py                    # DI wiring for the whole dependency graph
│   │   └── v1/
│   │       └── resume.py              # upload, parse, and get-parsed-data routes
│   ├── core/
│   │   ├── config.py                  # Settings (pydantic-settings, loads .env)
│   │   └── logger.py                  # Centralized logging configuration
│   ├── db/
│   │   └── database.py                # Async engine, session factory, Base
│   ├── models/                        # SQLAlchemy 2.0 ORM models
│   │   ├── resume.py                  #   Resume, ResumeStatus
│   │   ├── personal_info.py           #   PersonalInfo (1:1 with Resume)
│   │   ├── social_profile.py          #   SocialProfile, SocialPlatform
│   │   ├── education.py               #   Education
│   │   ├── experience.py              #   Experience
│   │   ├── skill.py                   #   Skill (global catalog), ResumeSkill (join table)
│   │   ├── certification.py           #   Certification
│   │   └── project.py                 #   Project
│   ├── repositories/                  # Only layer that touches the DB session
│   │   ├── resume_repository.py       #   Resume CRUD
│   │   └── parsed_resume_repository.py#   Parsed-data aggregate: save (transactional) + fetch
│   ├── services/
│   │   ├── upload_service.py          # Upload validation, storage, persistence
│   │   ├── parser_service.py          # Pure: PDF bytes -> ParsedResumeData (no DB/disk)
│   │   ├── resume_parsing_service.py  # Orchestration: fetch, dedupe-guard, parse, persist
│   │   └── extractors/                # One module per extraction concern
│   │       ├── text_extractor.py      #   PyMuPDF text extraction + cleaning
│   │       ├── section_splitter.py    #   Splits text into named sections by header line
│   │       ├── contact_extractor.py   #   Name (heuristic + spaCy fallback), email, phone, address
│   │       ├── social_extractor.py    #   LinkedIn/GitHub/Twitter/Medium/portfolio URLs
│   │       ├── skill_extractor.py     #   Keyword matching against utils/skills.py
│   │       ├── education_extractor.py
│   │       ├── experience_extractor.py
│   │       ├── project_extractor.py
│   │       └── certification_extractor.py
│   ├── schemas/
│   │   ├── resume.py                  # Upload request/response models
│   │   └── parsed_resume.py           # Parsed-data models (shared by service/repo/API)
│   ├── utils/
│   │   ├── file_utils.py              # Pure filesystem helpers
│   │   ├── skills.py                  # Predefined technical-skill catalog
│   │   └── date_utils.py              # dateparser-based single-date/date-range parsing
│   ├── middleware/
│   │   └── exception_handler.py       # Global exception handlers -> consistent JSON errors
│   ├── exceptions/
│   │   └── custom_exceptions.py       # AppException hierarchy
│   └── main.py                        # FastAPI app, routes, lifespan, handler registration
├── uploads/                            # PDF storage (bind-mounted volume)
├── tests/                              # Pytest suite (in-memory SQLite, no Docker required)
│   └── fixtures/pdf_builder.py         # Builds synthetic test PDFs with PyMuPDF itself
├── alembic/                            # Migrations (async env.py)
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
└── README.md
```

## Architecture & Design Decisions

### Phase 1 (upload)

- **Clean Architecture / layered separation.** Routes only translate HTTP
  <-> schemas and delegate to services. Services hold all business logic and
  depend on repository abstractions, not the DB session. Repositories are the
  only layer that touches the SQLAlchemy session.
- **Dependency Injection via FastAPI `Depends`.** `app/api/deps.py` builds
  the entire dependency graph in one place.
- **Async end-to-end**, with disk writes pushed to a thread via
  `asyncio.to_thread` so they never block the event loop.
- **UUID storage filenames** (`uploads/<uuid4>.pdf`) eliminate path-traversal
  and collision concerns — duplicate original filenames are explicitly allowed.
- **SQLAlchemy 2.0 `Uuid` / `Enum` generic types** (not `postgresql.UUID`)
  keep models dialect-agnostic, which is what lets the test suite run against
  SQLite with zero special-casing.
- **Custom exception hierarchy + global handlers** translate every error path
  into one consistent envelope: `{"success": false, "message": "..."}`.

### Phase 2 (parsing)

- **`ParserService` is pure — no DB, no disk.** It takes raw PDF bytes and
  returns a `ParsedResumeData` object. All persistence and resume-lookup
  concerns live in `ResumeParsingService` (the orchestrator), so the parser
  is trivially unit-testable with synthetic PDF bytes and no test database.

- **One extractor module per entity type**, each with a single, narrow
  responsibility (SRP): `text_extractor` only turns PDF bytes into clean
  text; `section_splitter` only groups lines under a detected header;
  `contact_extractor`, `social_extractor`, `skill_extractor`,
  `education_extractor`, `experience_extractor`, `project_extractor`, and
  `certification_extractor` each own one entity's regex/heuristic logic.
  `project_extractor` reuses `skill_extractor` to tag technologies mentioned
  in a project's description when no explicit "Technologies:" line is
  present, instead of a second keyword list.

- **Section-first extraction.** Cleaned text is split into named sections
  (`header`, `summary`, `skills`, `education`, `experience`, `projects`,
  `certifications`) by detecting header lines that *entirely* match a known
  alias (e.g. "Skills", "Technical Skills", "Work Experience"). Each
  extractor then runs against its own section instead of the whole document,
  which sharply reduces false positives (e.g. a CGPA or a project's
  version number never gets misread as a phone number).

- **Regex + dateparser, no ML/LLM**, per the Phase 2 requirement. Date
  ranges ("Jan 2020 - Present", "2019 - 2021", "03/2021 - 08/2022") are
  parsed once, centrally, in `utils/date_utils.py` and reused by both the
  education and experience extractors — not reimplemented per extractor.

- **spaCy is an optional enhancement, not a hard dependency at runtime.**
  `contact_extractor.extract_name()` first tries a positional heuristic (a
  short, title-cased line with no digits/@/URL near the top of the resume);
  only if that fails does it lazily load spaCy's `en_core_web_sm` model and
  fall back to PERSON named-entity recognition. If the model isn't
  installed, this is logged once and parsing continues on heuristics alone
  — a missing NLP model never turns into a request failure.

- **Skills are a normalized many-to-many catalog.** `Skill` is a global,
  deduplicated table (`skills.name` is unique); `ResumeSkill` links a resume
  to the skills found in it. `ParsedResumeRepository._get_or_create_skill()`
  reuses an existing `Skill` row across resumes instead of inserting
  duplicates. The API still returns `skills` as a flat list of strings —
  the normalization is a storage decision, not something API clients need
  to deal with.

- **`ParsedResumeRepository` treats 7 tables as one aggregate**, not seven
  independent repositories. `PersonalInfo`, `SocialProfile`, `Education`,
  `Experience`, `Skill`/`ResumeSkill`, `Certification`, and `Project` are
  always written together (one parse = one transaction, via
  `save_parsed_data()`) and always read together (one `GET .../parsed` =
  one fetch, via `get_by_resume_id()`). `save_parsed_data()` commits once at
  the end and rolls back the entire set on any failure — a resume never ends
  up with partially-saved parsed data.

- **Duplicate-parse detection doesn't touch `Resume.status`.** Phase 1's
  `ResumeStatus` enum (`UPLOADED`/`FAILED`) is left untouched, per "don't
  break Phase 1." Instead, `ResumeParsingService.parse_resume()` checks
  `ParsedResumeRepository.exists_for_resume()` (a `PersonalInfo` row already
  existing for that `resume_id`) and raises `DuplicateParseException` (409)
  if so.

- **Error handling reuses Phase 1's exception infrastructure.**
  `ResumeNotFoundException` (404), `CorruptedPdfException` /
  `EncryptedPdfException` / `EmptyPdfException` (422 — the request was
  well-formed but the file content can't be processed),
  `DuplicateParseException` (409), and `ParsedDataNotFoundException` (404)
  all extend the existing `AppException` and are handled by the same global
  handler from Phase 1 — no new middleware was needed. A missing file *on
  disk* (DB record exists, but the PDF is gone) reuses `StorageException`
  (500), since that's a server-side storage-integrity failure, not a client
  error.

- **`Experience.is_current`** is an explicit boolean rather than inferring
  "current job" from `end_date IS NULL` alone, because `end_date` can
  legitimately be `NULL` for two different reasons (unparseable date vs.
  "Present") and the spec requires distinguishing them.

- **Known heuristic limitations** (documented in-code, not silently hidden):
  phone-number matching accepts any 10-15 digit span rather than validating
  a real numbering plan; address extraction is a best-effort comma+digits
  heuristic; company/title splitting relies on common separators (" at ",
  " | ", " - "); a small number of skills (e.g. "Go", "R") can collide with
  ordinary English words. These are accepted trade-offs for a regex-based,
  non-ML parser — the alternative (a bespoke NLP model) is explicitly out of
  scope for Phase 2.

## Environment Variables

| Variable            | Description                                   | Default (see `.env.example`) |
|---------------------|------------------------------------------------|-------------------------------|
| `APP_NAME`          | Service name shown in OpenAPI docs             | `Resume Parsing Service`     |
| `DEBUG`             | Enables SQL echo + verbose logging             | `True`                       |
| `DATABASE_URL`      | Async SQLAlchemy URL (`asyncpg` driver)        | `postgresql+asyncpg://...`   |
| `UPLOAD_DIRECTORY`  | Directory PDFs are written to                  | `uploads`                    |
| `MAX_FILE_SIZE`     | Max upload size in bytes                       | `10485760` (10 MB)           |

Copy `.env.example` to `.env` and adjust before running.

## Setup Commands

```bash
cd backend
cp .env.example .env

# Option A: Docker (recommended — starts Postgres too, and downloads the
# spaCy model as part of the image build)
docker compose up --build -d

# Option B: Local virtualenv (requires a running Postgres yourself)
python -m venv .venv
source .venv/Scripts/activate   # Windows Git Bash; use .venv\Scripts\Activate.ps1 on PowerShell
pip install -r requirements.txt
python -m spacy download en_core_web_sm   # optional: enables NER-based name fallback
```

## Database Migrations (Alembic)

Run these from `backend/` with the virtualenv active (or
`docker compose exec api ...` if using Docker):

```bash
# Apply all migrations
alembic upgrade head

# After changing a model, generate a new migration
alembic revision --autogenerate -m "Describe the change"
```

Migrations:
- `202608040001_initial.py` — creates `resumes` (Phase 1).
- `202608040002_add_parsed_resume_tables.py` — creates `personal_info`,
  `social_profiles`, `education`, `experience`, `skills`, `resume_skills`,
  `certifications`, `projects`, each FK'd to `resumes.id` with
  `ON DELETE CASCADE` (Phase 2).

## Run Commands

```bash
# Docker (API on http://localhost:8000)
docker compose up --build

# Local (requires `alembic upgrade head` run first, and Postgres reachable
# at DATABASE_URL)
uvicorn app.main:app --reload
```

## API Documentation

Once running: Swagger UI at `http://localhost:8000/docs`, ReDoc at
`http://localhost:8000/redoc`, raw OpenAPI schema at
`http://localhost:8000/openapi.json`.

### Endpoints

| Method | Path                                  | Description                                   |
|--------|----------------------------------------|------------------------------------------------|
| GET    | `/`                                    | Service info                                    |
| GET    | `/health`                              | Health check                                    |
| POST   | `/api/v1/resumes/upload`               | Upload a PDF resume (max 10MB)                  |
| POST   | `/api/v1/resumes/{resume_id}/parse`    | Parse an uploaded resume into structured data   |
| GET    | `/api/v1/resumes/{resume_id}/parsed`   | Fetch a resume's previously parsed data         |

`POST .../parse` and `GET .../parsed` both return:

```json
{
  "success": true,
  "resume_id": "...",
  "parsed": {
    "personal_info": {"full_name": "...", "email": "...", "phone": "...", "address": "...", "summary": "..."},
    "skills": ["..."],
    "education": [{"institution": "...", "degree": "...", "field_of_study": "...", "start_date": "...", "end_date": "...", "grade": "..."}],
    "experience": [{"company": "...", "job_title": "...", "location": "...", "start_date": "...", "end_date": "...", "is_current": false, "description": "..."}],
    "projects": [{"name": "...", "description": "...", "technologies": "..."}],
    "certifications": [{"name": "...", "issuer": "...", "date": "..."}],
    "social_profiles": [{"platform": "LINKEDIN", "url": "..."}]
  }
}
```

`POST .../parse` error cases: `404` resume not found, `409` already parsed,
`422` corrupted/encrypted/empty PDF, `500` stored file missing from disk or a
persistence failure.

## Test Commands

Tests run against an in-memory SQLite database and a temporary directory —
**no Docker or Postgres required**:

```bash
cd backend
pip install -r requirements.txt
pytest -v
```

- `test_health.py` — root and health endpoints.
- `test_upload.py` — valid PDF upload, reject PNG, reject oversized file, reject missing file.
- `test_parser_service.py` — unit tests against `ParserService` directly
  (no DB/HTTP), using synthetic PDFs built at test time with PyMuPDF itself
  (`tests/fixtures/pdf_builder.py`): a full resume, a resume without
  experience, a resume without education, a multi-page resume, a corrupted
  PDF, an encrypted PDF, an empty PDF, skill/email/phone extraction.
- `test_parse_api.py` — integration tests through the HTTP client: parse a
  valid uploaded resume, fetch parsed data, fetch before parsing (404),
  duplicate parse (409), parse a nonexistent resume (404).

## Git Commit Message

```
feat: implement resume parsing engine and structured data extraction
```
