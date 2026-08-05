"""Rejects requests whose body is larger than the configured hard cap.

This is a coarse, early defense (checked from the `Content-Length` header
before any parsing happens) — distinct from `MAX_FILE_SIZE`, which is the
business-rule check `UploadService` applies to the PDF content itself.
A request without a `Content-Length` header (e.g. chunked transfer
encoding) is not rejected here; it still passes through the normal
upload-size validation downstream.
"""

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response


class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, *, max_body_size: int) -> None:
        super().__init__(app)
        self._max_body_size = max_body_size

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        content_length = request.headers.get("content-length")
        if content_length is not None:
            try:
                size = int(content_length)
            except ValueError:
                size = None
            if size is not None and size > self._max_body_size:
                return JSONResponse(
                    status_code=413,
                    content={
                        "success": False,
                        "message": (
                            f"Request body exceeds the maximum allowed size of "
                            f"{self._max_body_size} bytes."
                        ),
                    },
                )
        return await call_next(request)
