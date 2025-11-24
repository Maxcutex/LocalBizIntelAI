"""HTTP endpoint tests for health routes."""


def test_health_check(client):
    """`GET /health/` returns ok status."""
    response = client.get("/health/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
