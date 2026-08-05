"""Tests the rate-limiting mechanism itself.

The main app's routes use a generous rate limit in tests (see
`conftest.py` — widened via env vars because the limit is baked into the
route decorators at import time and the full suite's call volume would
otherwise trip a production-sized limit). To verify the underlying
blocking behavior deterministically, this test mounts a tiny standalone
app using the same shared `limiter` instance with a very low limit,
independent of the main app's state.
"""

from fastapi import FastAPI, Request, Response
from httpx import ASGITransport, AsyncClient
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.core.rate_limiter import limiter


async def test_limiter_blocks_requests_beyond_the_configured_rate() -> None:
    probe_app = FastAPI()
    probe_app.state.limiter = limiter
    probe_app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    @probe_app.get("/probe")
    @limiter.limit("3/minute")
    async def probe(request: Request, response: Response) -> dict:
        return {"ok": True}

    transport = ASGITransport(app=probe_app)
    async with AsyncClient(transport=transport, base_url="http://ratelimit-test") as client:
        statuses = [(await client.get("/probe")).status_code for _ in range(4)]

    assert statuses[:3] == [200, 200, 200]
    assert statuses[3] == 429
