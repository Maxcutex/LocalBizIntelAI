"""Unit tests for request logging middleware."""

import logging

from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.config import Settings
from api.request_logging_middleware import RequestLoggingMiddleware


def test_request_logging_middleware_adds_request_id_and_logs(caplog) -> None:
    app = FastAPI()
    settings = Settings(log_request_body=True, log_response_body=True)
    app.add_middleware(RequestLoggingMiddleware, settings=settings)

    @app.post("/echo")
    def echo(payload: dict) -> dict:
        return payload

    client = TestClient(app)
    with caplog.at_level(logging.INFO):
        resp = client.post("/echo", json={"password": "secret", "x": 1})

    assert resp.status_code == 200
    assert "X-Request-Id" in resp.headers
    # Ensure we logged a completion line and redacted password.
    messages = [r.message for r in caplog.records]
    assert any("Request completed" in m for m in messages)
    assert any(
        "***REDACTED***" in str(r.__dict__.get("fields")) for r in caplog.records
    )
