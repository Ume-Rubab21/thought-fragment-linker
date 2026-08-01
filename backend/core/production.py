from __future__ import annotations

import os
import time
import uuid
from collections import defaultdict, deque
from threading import Lock

from fastapi import Request
from fastapi.responses import JSONResponse


def _csv_env(name: str, default: str = "") -> list[str]:
    return [value.strip() for value in os.getenv(name, default).split(",") if value.strip()]


def allowed_origins() -> list[str]:
    origins = _csv_env(
        "CORS_ALLOWED_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173",
    )
    return origins or ["http://localhost:5173"]


class SimpleRateLimiter:
    """Small in-process limiter suitable for one Railway worker.

    For multiple workers/replicas, replace this with Redis-backed limits.
    """

    def __init__(self, requests: int = 120, window_seconds: int = 60) -> None:
        self.requests = max(1, requests)
        self.window_seconds = max(1, window_seconds)
        self._events: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def allow(self, key: str) -> tuple[bool, int]:
        now = time.monotonic()
        cutoff = now - self.window_seconds
        with self._lock:
            events = self._events[key]
            while events and events[0] <= cutoff:
                events.popleft()
            if len(events) >= self.requests:
                retry_after = max(1, int(self.window_seconds - (now - events[0])))
                return False, retry_after
            events.append(now)
            return True, 0


RATE_LIMITER = SimpleRateLimiter(
    requests=int(os.getenv("RATE_LIMIT_REQUESTS", "120")),
    window_seconds=int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60")),
)


async def production_guard_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    client_host = request.client.host if request.client else "unknown"

    exempt = request.url.path in {"/health", "/health/ready"}
    if not exempt:
        allowed, retry_after = RATE_LIMITER.allow(client_host)
        if not allowed:
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Too many requests. Please try again shortly.",
                    "request_id": request_id,
                },
                headers={"Retry-After": str(retry_after), "X-Request-ID": request_id},
            )

    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    return response
