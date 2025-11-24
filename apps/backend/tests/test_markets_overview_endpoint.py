"""HTTP endpoint tests for market overview routes."""

from uuid import UUID, uuid4

from api.dependencies import CurrentRequestContext, get_current_request_context, get_db
from api.main import create_app
from api.routers import markets as markets_router


def override_db():
    """Provide a dummy DB session for dependency overrides."""

    class DummySession:
        """Stub SQLAlchemy session."""

    yield DummySession()


def test_get_market_overview_success():
    """`GET /markets/{city}/overview` returns overview for valid auth."""
    app = create_app()
    tenant_id = uuid4()

    class FakeMarketService:
        """Fake market service used to validate router wiring."""

        def get_overview(
            self,
            _db_session,
            city: str,
            country: str | None,
            requested_tenant_id: UUID,
        ):
            """Return a canned overview response."""
            assert city == "Accra"
            assert country == "GH"
            assert requested_tenant_id == tenant_id
            return {"city": city, "country": country, "ok": True}

    def override_context():
        """Provide a fake request context with tenant/user ids."""
        return CurrentRequestContext(user_id=uuid4(), tenant_id=tenant_id)

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_request_context] = override_context

    def override_market_service():
        """Provide the fake market service."""
        return FakeMarketService()

    app.dependency_overrides[markets_router.get_market_service] = (
        override_market_service
    )

    from fastapi.testclient import TestClient

    client = TestClient(app)
    response = client.get("/markets/Accra/overview?country=GH")

    assert response.status_code == 200
    assert response.json() == {"city": "Accra", "country": "GH", "ok": True}


def test_get_market_overview_missing_headers_returns_401():
    """Missing auth headers returns 401."""
    app = create_app()
    app.dependency_overrides[get_db] = override_db

    from fastapi.testclient import TestClient

    client = TestClient(app)
    response = client.get("/markets/Accra/overview")

    assert response.status_code == 401


def test_get_market_overview_invalid_headers_returns_400():
    """Invalid auth headers returns 400."""
    app = create_app()
    app.dependency_overrides[get_db] = override_db

    from fastapi.testclient import TestClient

    client = TestClient(app)
    response = client.get(
        "/markets/Accra/overview",
        headers={
            "X-User-Id": "invalid",
            "X-Tenant-Id": "invalid",
        },
    )

    assert response.status_code == 400
