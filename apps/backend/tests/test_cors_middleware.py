import os

from api.config import get_settings
from api.main import create_app


def test_cors_allows_configured_origin():
    os.environ["CORS_ALLOWED_ORIGINS"] = "https://example.com"
    get_settings.cache_clear()
    try:
        app = create_app()

        from fastapi.testclient import TestClient

        client = TestClient(app)
        response = client.options(
            "/health/",
            headers={
                "Origin": "https://example.com",
                "Access-Control-Request-Method": "GET",
            },
        )

        assert response.status_code in (200, 204)
        assert (
            response.headers.get("access-control-allow-origin") == "https://example.com"
        )
    finally:
        os.environ.pop("CORS_ALLOWED_ORIGINS", None)
        get_settings.cache_clear()
