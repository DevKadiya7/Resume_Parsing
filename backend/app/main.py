"""FastAPI application entrypoint."""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.v1 import resume
from app.core.config import get_settings
from app.core.logger import get_logger
from app.middleware.exception_handler import register_exception_handlers
from app.utils.file_utils import ensure_directory_exists

settings = get_settings()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    ensure_directory_exists(settings.UPLOAD_DIRECTORY)
    logger.info("%s starting up (debug=%s)", settings.APP_NAME, settings.DEBUG)
    yield
    logger.info("%s shutting down", settings.APP_NAME)


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "Accepts PDF resumes, stores them, and extracts structured data "
        "(personal info, skills, education, experience, projects, "
        "certifications, social profiles) using PyMuPDF, regex, spaCy, "
        "and dateparser — no LLM or external AI API."
    ),
    lifespan=lifespan,
)

register_exception_handlers(app)

app.include_router(resume.router, prefix="/api/v1")


@app.get("/", summary="Service info", tags=["Meta"])
async def root() -> dict[str, str]:
    return {"message": "Resume Parsing Service"}


@app.get("/health", summary="Health check", tags=["Meta"])
async def health() -> dict[str, str]:
    return {"status": "healthy"}
