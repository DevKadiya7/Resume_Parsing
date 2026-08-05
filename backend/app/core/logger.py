"""Centralized logging configuration.

All application modules obtain their logger via `get_logger(__name__)`
rather than calling `logging.getLogger` directly, so log formatting and
handlers stay defined in exactly one place. Every log record automatically
carries the current request's ID (see `app.core.request_context`), and the
output format — human-readable text or structured JSON — is controlled by
`Settings.LOG_FORMAT` so production deployments can feed logs to an
aggregator without a separate parsing step.
"""

import json
import logging
import sys
from datetime import datetime, timezone

from app.core.config import get_settings
from app.core.request_context import get_request_id

_TEXT_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | [%(request_id)s] | %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

_configured = False


class _RequestIdFilter(logging.Filter):
    """Attaches the current request's ID (or "-" outside a request) to every record."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = get_request_id() or "-"
        return True


class _JsonFormatter(logging.Formatter):
    """Renders each log record as a single-line JSON object."""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": getattr(record, "request_id", "-"),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload)


def configure_logging() -> None:
    """Configure the root logger. Safe to call multiple times."""
    global _configured
    if _configured:
        return

    settings = get_settings()
    level = logging.DEBUG if settings.DEBUG else logging.INFO

    handler = logging.StreamHandler(sys.stdout)
    if settings.LOG_FORMAT == "json":
        handler.setFormatter(_JsonFormatter())
    else:
        handler.setFormatter(logging.Formatter(_TEXT_FORMAT, datefmt=_DATE_FORMAT))
    handler.addFilter(_RequestIdFilter())

    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.handlers.clear()
    root_logger.addHandler(handler)

    # Keep noisy third-party loggers at a reasonable level.
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)

    _configured = True


def get_logger(name: str) -> logging.Logger:
    """Return a module-scoped logger, ensuring logging is configured first."""
    configure_logging()
    return logging.getLogger(name)
