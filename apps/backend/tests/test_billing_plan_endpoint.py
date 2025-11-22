from uuid import UUID, uuid4

from api.dependencies import CurrentRequestContext, get_current_request_context, get_db
from api.main import create_app
from api.routers import billing as billing_router


def override_db():
    class DummySession:
        pass

    yield DummySession()


def test_get_plan_success():
    app = create_app()
    tenant_id = uuid4()

    class FakeBillingService:
        def get_plan_and_usage(self, db_session, requested_tenant_id: UUID):
            assert requested_tenant_id == tenant_id
            return {"plan": "pro", "status": "active", "usage": {"reports": 2}}

    def override_context():
        return CurrentRequestContext(user_id=uuid4(), tenant_id=tenant_id)

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_request_context] = override_context
    app.dependency_overrides[billing_router.get_billing_service] = (
        lambda: FakeBillingService()
    )

    from fastapi.testclient import TestClient

    client = TestClient(app)
    response = client.get("/billing/plan")

    assert response.status_code == 200
    assert response.json()["plan"] == "pro"


def test_get_plan_missing_headers_returns_401():
    app = create_app()
    app.dependency_overrides[get_db] = override_db

    from fastapi.testclient import TestClient

    client = TestClient(app)
    response = client.get("/billing/plan")

    assert response.status_code == 401
