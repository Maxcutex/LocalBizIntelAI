"""Unit tests for request logging middleware."""

import logging
from contextlib import contextmanager
from typing import Any

from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.config import Settings
from api.request_logging_middleware import RequestLoggingMiddleware


@contextmanager
def _disable_dotenv_for_settings() -> Any:
    old_env_file = Settings.model_config.get("env_file")
    Settings.model_config["env_file"] = None
    try:
        yield
    finally:
        Settings.model_config["env_file"] = old_env_file


def test_request_logging_middleware_adds_request_id_and_logs(caplog) -> None:
    app = FastAPI()
    with _disable_dotenv_for_settings():
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
    # Ensure we logged a completion line and redacted password in request_body.
    completed_records = [r for r in caplog.records if r.message == "Request completed"]
    assert completed_records
    assert any(
        (r.__dict__.get("request_body") or {}).get("password") == "***REDACTED***"
        for r in completed_records
    )
