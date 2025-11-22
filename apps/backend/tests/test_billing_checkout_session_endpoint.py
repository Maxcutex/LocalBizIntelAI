from uuid import UUID, uuid4

from api.dependencies import CurrentRequestContext, get_current_request_context, get_db
from api.main import create_app
from api.routers import billing as billing_router


def override_db():
    class DummySession:
        pass

    yield DummySession()


def test_create_checkout_session_success():
    app = create_app()
    tenant_id = uuid4()

    class FakeBillingService:
        def create_checkout_session(
            self, db_session, requested_tenant_id: UUID, target_plan: str
        ):
            assert requested_tenant_id == tenant_id
            assert target_plan == "pro"
            return {"checkout_session_id": "cs_1", "url": "https://x"}

    def override_context():
        return CurrentRequestContext(user_id=uuid4(), tenant_id=tenant_id)

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_request_context] = override_context
    app.dependency_overrides[billing_router.get_billing_service] = (
        lambda: FakeBillingService()
    )

    from fastapi.testclient import TestClient

    client = TestClient(app)
    response = client.post("/billing/checkout-session", json={"target_plan": "pro"})

    assert response.status_code == 200
    assert response.json()["checkout_session_id"] == "cs_1"


def test_create_checkout_session_missing_headers_returns_401():
    app = create_app()
    app.dependency_overrides[get_db] = override_db

    from fastapi.testclient import TestClient

    client = TestClient(app)
    response = client.post("/billing/checkout-session", json={"target_plan": "pro"})

    assert response.status_code == 401
