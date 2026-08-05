"""Rate limiter shared across routes that need per-endpoint throttling.

Built on slowapi (a Starlette-friendly wrapper around the `limits`
library) with in-memory storage — sufficient for a single-process
deployment. A multi-instance deployment would point this at Redis via
`Limiter(storage_uri="redis://...")` instead, without changing any route
code, since routes only ever reference this shared `limiter` instance.
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address, headers_enabled=True)
