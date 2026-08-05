"""Assigns a unique ID to every request.

Accepts an inbound `X-Request-ID` header (useful when a gateway/load
balancer already generates one) and otherwise mints a new UUID4. The ID is
stored in a `ContextVar` (picked up automatically by every log line — see
`app.core.logger`), attached to `request.state`, and echoed back on the
response so callers can correlate their request with server-side logs.
"""

import uuid

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from app.core.request_context import set_request_id

_HEADER_NAME = "X-Request-ID"


class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        request_id = request.headers.get(_HEADER_NAME) or str(uuid.uuid4())
        set_request_id(request_id)
        request.state.request_id = request_id

        response = await call_next(request)
        response.headers[_HEADER_NAME] = request_id
        return response
