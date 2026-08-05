"""FastAPI application entrypoint."""

import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.api.v1 import resume
from app.core.config import get_settings
from app.core.logger import get_logger
from app.core.rate_limiter import limiter
from app.db.database import get_db
from app.middleware.exception_handler import register_exception_handlers
from app.middleware.logging_middleware import RequestLoggingMiddleware
from app.middleware.request_id_middleware import RequestIDMiddleware
from app.middleware.security_headers_middleware import SecurityHeadersMiddleware
from app.middleware.size_limit_middleware import RequestSizeLimitMiddleware
from app.utils.file_utils import ensure_directory_exists

settings = get_settings()
logger = get_logger(__name__)

_start_time = time.monotonic()


@asynccontextmanager
async def lifespan(app: FastAPI):
    ensure_directory_exists(settings.UPLOAD_DIRECTORY)
    logger.info(
        "%s starting up (environment=%s, debug=%s, version=%s)",
        settings.APP_NAME,
        settings.ENVIRONMENT.value,
        settings.DEBUG,
        settings.APP_VERSION,
    )
    yield
    logger.info("%s shutting down", settings.APP_NAME)


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "Accepts PDF resumes, stores them, and extracts structured data "
        "(personal info, skills, education, experience, projects, "
        "certifications, social profiles) using PyMuPDF, regex, spaCy, "
        "and dateparser — no LLM or external AI API. Also provides "
        "paginated listing, multi-field search, filtering, statistics, "
        "deletion, and download over the parsed corpus."
    ),
    lifespan=lifespan,
)

app.state.limiter = limiter
# slowapi's handler is typed for its specific exception subclass, which
# mypy sees as incompatible with Starlette's broader `Exception` handler
# signature — a known, benign mismatch between the two libraries' stubs.
app.add_exception_handler(
    RateLimitExceeded, _rate_limit_exceeded_handler  # type: ignore[arg-type]
)

register_exception_handlers(app)

# Middleware is applied outer-to-inner in the *reverse* of the order added
# below (Starlette wraps each new middleware around the previous stack), so
# the last one added here — TrustedHostMiddleware — runs first on every
# request, and SecurityHeadersMiddleware, added first, runs closest to the
# route handlers.
app.add_middleware(
    SecurityHeadersMiddleware, enable_hsts=settings.ENVIRONMENT.value == "production"
)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(RequestIDMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID", "X-Response-Time-Ms"],
)
app.add_middleware(RequestSizeLimitMiddleware, max_body_size=settings.MAX_REQUEST_SIZE)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.ALLOWED_HOSTS)

app.include_router(resume.router, prefix="/api/v1")


@app.get("/", summary="Service info", tags=["Meta"])
async def root() -> dict[str, str]:
    return {"message": "Resume Parsing Service"}


@app.get(
    "/health",
    summary="Health check",
    tags=["Meta"],
    description=(
        "Liveness/readiness probe. Reports database connectivity, upload "
        "directory availability, application version, and process uptime."
    ),
)
async def health(db: Annotated[AsyncSession, Depends(get_db)]) -> dict:
    database_status = "connected"
    try:
        await db.execute(text("SELECT 1"))
    except Exception:
        logger.exception("Health check: database connection failed")
        database_status = "error"

    upload_dir = Path(settings.UPLOAD_DIRECTORY)
    upload_directory_status = "ok" if upload_dir.exists() and upload_dir.is_dir() else "missing"

    is_healthy = database_status == "connected" and upload_directory_status == "ok"
    overall_status = "healthy" if is_healthy else "degraded"

    return {
        "status": overall_status,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT.value,
        "uptime_seconds": round(time.monotonic() - _start_time, 2),
        "database": database_status,
        "upload_directory": upload_directory_status,
    }
