"""HTTP endpoint tests for persona generation routes."""

from uuid import UUID, uuid4

from api.dependencies import CurrentRequestContext, get_current_request_context, get_db
from api.main import create_app
from api.routers import personas as personas_router


def override_db():
    """Provide a dummy DB session for dependency overrides."""

    class DummySession:
        """Stub SQLAlchemy session."""

    yield DummySession()


def test_generate_personas_success():
    """`POST /personas/generate` succeeds with valid auth and payload."""
    app = create_app()
    expected_tenant_id = uuid4()

    class FakePersonaService:
        """Fake persona service asserting router wiring."""

        def generate_personas(
            self,
            db_session,
            city: str,
            country: str | None,
            geo_ids: list[str] | None,
            business_type: str | None,
            tenant_id: UUID,
        ):
            """Return deterministic personas payload."""
            _ = db_session
            assert city == "Accra"
            assert country == "GH"
            assert geo_ids == ["accra-1"]
            assert business_type == "retail"
            assert tenant_id == expected_tenant_id
            return {
                "city": city,
                "country": country,
                "business_type": business_type,
                "personas": {"headline": "ok", "personas": []},
            }

    def override_context():
        """Provide a fake request context with user and tenant ids."""
        return CurrentRequestContext(user_id=uuid4(), tenant_id=expected_tenant_id)

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_request_context] = override_context

    def override_persona_service():
        """Provide the fake persona service."""
        return FakePersonaService()

    app.dependency_overrides[personas_router.get_persona_service] = (
        override_persona_service
    )

    from fastapi.testclient import TestClient

    client = TestClient(app)
    response = client.post(
        "/personas/generate",
        json={
            "city": "Accra",
            "country": "GH",
            "geo_ids": ["accra-1"],
            "business_type": "retail",
        },
    )

    assert response.status_code == 200
    assert response.json()["personas"]["headline"] == "ok"


def test_generate_personas_missing_headers_returns_401():
    """Missing auth headers yields 401."""
    app = create_app()
    app.dependency_overrides[get_db] = override_db

    from fastapi.testclient import TestClient

    client = TestClient(app)
    response = client.post("/personas/generate", json={"city": "Accra"})

    assert response.status_code == 401
