"""HTTP request/response logging middleware.

Logs high-signal request/response metadata for every call, and can optionally
log request/response bodies (JSON only, truncated and redacted).

This is the canonical place for route-level logging without duplicating per-route.
"""

from __future__ import annotations

import json
import logging
import time
import uuid
from typing import Any

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response as StarletteResponse

from api.config import Settings

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Structured request/response logger for FastAPI."""

    def __init__(self, app: Any, *, settings: Settings) -> None:
        super().__init__(app)
        self._settings = settings

    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = request.headers.get("X-Request-Id") or str(uuid.uuid4())
        start = time.perf_counter()

        request_body_repr: Any | None = None
        if self._settings.log_request_body:
            request_body_repr = await self._read_body_repr(request)

        try:
            response = await call_next(request)
        except Exception:
            duration_ms = int((time.perf_counter() - start) * 1000)
            logger.error(
                "Request failed",
                exc_info=True,
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": str(request.url.path),
                    "query": str(request.url.query) or None,
                    "duration_ms": duration_ms,
                    "request_body": request_body_repr,
                },
            )
            raise

        response_body_bytes: bytes | None = None
        if self._settings.log_response_body:
            response_body_bytes, response = await self._capture_response_body(response)

        duration_ms = int((time.perf_counter() - start) * 1000)
        extra = {
            "request_id": request_id,
            "method": request.method,
            "path": str(request.url.path),
            "query": str(request.url.query) or None,
            "status_code": response.status_code,
            "duration_ms": duration_ms,
            "client_ip": request.client.host if request.client else None,
        }
        if self._settings.log_request_body:
            extra["request_body"] = request_body_repr
        if self._settings.log_response_body:
            extra["response_body"] = self._body_bytes_to_repr(
                response_body_bytes or b"", response.media_type
            )

        logger.info("Request completed", extra=extra)
        response.headers["X-Request-Id"] = request_id
        return response

    async def _read_body_repr(self, request: Request) -> Any | None:
        body_bytes = await request.body()
        # Reset request stream so downstream handlers can read again.
        request._body = body_bytes  # type: ignore[attr-defined,protected-access]
        return self._body_bytes_to_repr(body_bytes, request.headers.get("content-type"))

    def _body_bytes_to_repr(self, body: bytes, content_type: str | None) -> Any | None:
        if not body:
            return None
        truncated = body[: self._settings.log_body_max_bytes]

        if content_type and "application/json" in content_type.lower():
            try:
                parsed = json.loads(truncated.decode("utf-8"))
                return self._redact(parsed)
            except Exception:
                return {"_raw": truncated.decode("utf-8", errors="replace")}

        # Non-JSON: log size only.
        return {"_bytes": len(body)}

    def _redact(self, value: Any) -> Any:
        if isinstance(value, dict):
            redacted: dict[str, Any] = {}
            for k, v in value.items():
                if k.lower() in {rk.lower() for rk in self._settings.log_redact_keys}:
                    redacted[k] = "***REDACTED***"
                else:
                    redacted[k] = self._redact(v)
            return redacted
        if isinstance(value, list):
            return [self._redact(v) for v in value]
        return value

    async def _capture_response_body(
        self, response: Response
    ) -> tuple[bytes, Response]:
        body = b""
        iterator = getattr(response, "body_iterator", None)
        if iterator is not None:
            async for chunk in iterator:
                body += chunk
        else:
            body = getattr(response, "body", b"") or b""

        new_response = StarletteResponse(
            content=body,
            status_code=response.status_code,
            headers=dict(response.headers),
            media_type=response.media_type,
        )
        return body, new_response
