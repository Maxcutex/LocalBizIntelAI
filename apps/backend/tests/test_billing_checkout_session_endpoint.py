"""HTTP endpoint tests for billing checkout-session route."""

from uuid import UUID, uuid4

from api.dependencies import CurrentRequestContext, get_current_request_context, get_db
from api.main import create_app
from api.routers import billing as billing_router


def override_db():
    """Provide a dummy DB session for dependency overrides."""

    class DummySession:
        """Stub SQLAlchemy session."""

    yield DummySession()


def test_create_checkout_session_success():
    """`POST /billing/checkout-session` succeeds with valid auth."""
    app = create_app()
    tenant_id = uuid4()

    class FakeBillingService:
        """Fake billing service asserting on input."""

        def create_checkout_session(
            self, _db_session, requested_tenant_id: UUID, target_plan: str
        ):
            """Return a canned checkout session."""
            assert requested_tenant_id == tenant_id
            assert target_plan == "pro"
            return {"checkout_session_id": "cs_1", "url": "https://x"}

    def override_context():
        """Provide a fake request context for auth headers."""
        return CurrentRequestContext(user_id=uuid4(), tenant_id=tenant_id)

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_request_context] = override_context

    def override_billing_service():
        """Provide the fake billing service."""
        return FakeBillingService()

    app.dependency_overrides[billing_router.get_billing_service] = (
        override_billing_service
    )

    from fastapi.testclient import TestClient

    client = TestClient(app)
    response = client.post("/billing/checkout-session", json={"target_plan": "pro"})

    assert response.status_code == 200
    assert response.json()["checkout_session_id"] == "cs_1"


def test_create_checkout_session_missing_headers_returns_401():
    """Missing auth headers yields 401."""
    app = create_app()
    app.dependency_overrides[get_db] = override_db

    from fastapi.testclient import TestClient

    client = TestClient(app)
    response = client.post("/billing/checkout-session", json={"target_plan": "pro"})

    assert response.status_code == 401
