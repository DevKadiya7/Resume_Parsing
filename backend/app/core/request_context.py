"""Request-scoped context shared between middleware and the logger.

A `ContextVar` is used (rather than threading a `request_id` parameter
through every function call) so any log statement anywhere in the call
stack can pick up the current request's ID automatically, via the
logging filter installed in `app.core.logger`.
"""

from contextvars import ContextVar

_request_id_ctx: ContextVar[str | None] = ContextVar("request_id", default=None)


def set_request_id(request_id: str) -> None:
    _request_id_ctx.set(request_id)


def get_request_id() -> str | None:
    return _request_id_ctx.get()
