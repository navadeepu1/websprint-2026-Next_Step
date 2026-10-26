import time
from collections import defaultdict, deque

from fastapi import Request
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.schemas.common import error_payload


def install_request_guards(app) -> None:
    windows: dict[str, deque[float]] = defaultdict(deque)

    @app.middleware("http")
    async def request_guards(request: Request, call_next):
        settings = get_settings()
        if request.method in {"POST", "PUT", "PATCH"}:
            length = request.headers.get("content-length")
            if length:
                try:
                    too_large = int(length) > settings.request_body_limit_bytes
                except ValueError:
                    return JSONResponse(status_code=400, content=error_payload("invalid_content_length", "Content-Length must be a number."))
                if too_large:
                    return JSONResponse(status_code=413, content=error_payload("request_too_large", "Request body is too large."))
        client = request.client.host if request.client else "unknown"
        now = time.monotonic()
        bucket = windows[client]
        while bucket and now - bucket[0] >= 60:
            bucket.popleft()
        if len(bucket) >= settings.rate_limit_per_minute:
            return JSONResponse(status_code=429, content=error_payload("rate_limited", "Too many requests. Try again shortly."))
        bucket.append(now)
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(settings.rate_limit_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(max(0, settings.rate_limit_per_minute - len(bucket)))
        return response
