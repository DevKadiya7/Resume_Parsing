"""Cross-cutting query-string validation shared by the listing/search routes."""

from fastapi import Request

from app.exceptions.custom_exceptions import InvalidQueryParameterException


def ensure_known_query_params(request: Request, allowed: set[str]) -> None:
    """Reject the request if it includes any query parameter not in `allowed`.

    FastAPI silently ignores unrecognized query parameters by default; this
    makes "unknown filter" an explicit 400 instead, per the API spec.
    """
    unknown = set(request.query_params.keys()) - allowed
    if unknown:
        raise InvalidQueryParameterException(
            f"Unknown query parameter(s): {', '.join(sorted(unknown))}"
        )
