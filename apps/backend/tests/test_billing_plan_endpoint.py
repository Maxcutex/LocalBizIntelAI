"""HTTP endpoint tests for billing plan route."""

from uuid import UUID, uuid4

from api.dependencies import CurrentRequestContext, get_current_request_context, get_db
from api.main import create_app
from api.routers import billing as billing_router


def override_db():
    """Provide a dummy DB session for dependency overrides."""

    class DummySession:
        """Stub SQLAlchemy session."""

    yield DummySession()


def test_get_plan_success():
    """`GET /billing/plan` returns plan for authorized tenant."""
    app = create_app()
    tenant_id = uuid4()

    class FakeBillingService:
        """Fake billing service returning canned plan/usage."""

        def get_plan_and_usage(self, _db_session, requested_tenant_id: UUID):
            """Return canned plan response."""
            assert requested_tenant_id == tenant_id
            return {"plan": "pro", "status": "active", "usage": {"reports": 2}}

    def override_context():
        """Provide fake request context with tenant id."""
        return CurrentRequestContext(user_id=uuid4(), tenant_id=tenant_id)

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_request_context] = override_context

    def override_billing_service():
        """Provide fake billing service."""
        return FakeBillingService()

    app.dependency_overrides[billing_router.get_billing_service] = (
        override_billing_service
    )

    from fastapi.testclient import TestClient

    client = TestClient(app)
    response = client.get("/billing/plan")

    assert response.status_code == 200
    assert response.json()["plan"] == "pro"


def test_get_plan_missing_headers_returns_401():
    """Missing auth headers yields 401."""
    app = create_app()
    app.dependency_overrides[get_db] = override_db

    from fastapi.testclient import TestClient

    client = TestClient(app)
    response = client.get("/billing/plan")

    assert response.status_code == 401
