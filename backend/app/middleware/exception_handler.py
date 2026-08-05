"""Global exception handlers.

Registered once on the FastAPI app so every error path — expected
(`AppException`), request-validation, HTTP, and unhandled — returns the
same JSON envelope: `{"success": false, "message": "..."}`.
"""

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.logger import get_logger
from app.exceptions.custom_exceptions import AppException

logger = get_logger(__name__)


def _error_response(message: str, status_code: int) -> JSONResponse:
    return JSONResponse(status_code=status_code, content={"success": False, "message": message})


def register_exception_handlers(app: FastAPI) -> None:
    """Attach all global exception handlers to the given FastAPI app."""

    @app.exception_handler(AppException)
    async def handle_app_exception(request: Request, exc: AppException) -> JSONResponse:
        logger.warning("Handled application error on %s: %s", request.url.path, exc.message)
        return _error_response(exc.message, exc.status_code)

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        logger.warning("Request validation failed on %s: %s", request.url.path, exc.errors())
        first_error = exc.errors()[0] if exc.errors() else None
        if first_error and first_error.get("loc", [None])[-1] == "file":
            message = "A file is required."
        else:
            message = "Invalid request."
        return _error_response(message, status.HTTP_422_UNPROCESSABLE_ENTITY)

    @app.exception_handler(StarletteHTTPException)
    async def handle_http_exception(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        return _error_response(str(exc.detail), exc.status_code)

    @app.exception_handler(Exception)
    async def handle_unhandled_exception(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled exception on %s", request.url.path)
        return _error_response(
            "An unexpected error occurred.", status.HTTP_500_INTERNAL_SERVER_ERROR
        )
