from uuid import uuid4

from api.dependencies import CurrentRequestContext, get_current_request_context, get_db
from api.main import create_app
from api.routers import etl as etl_router


def override_db():
    class DummySession:
        pass

    yield DummySession()


def test_admin_trigger_etl_success_and_payload_passed():
    app = create_app()
    expected_tenant_id = uuid4()
    expected_user_id = uuid4()

    class FakeEtlService:
        def trigger_adhoc_etl(
            self,
            db_session,
            dataset,
            country,
            city,
            options,
            triggered_by_user_id,
            triggered_by_tenant_id,
        ):
            assert dataset == "demographics"
            assert country == "GH"
            assert city == "Accra"
            assert options == {"force": True}
            assert triggered_by_user_id == expected_user_id
            assert triggered_by_tenant_id == expected_tenant_id
            return {
                "status": "QUEUED",
                "payload": {
                    "dataset": dataset,
                    "country": country,
                    "city": city,
                    "options": options,
                },
            }

    def override_context():
        return CurrentRequestContext(
            user_id=expected_user_id, tenant_id=expected_tenant_id, role="ADMIN"
        )

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_request_context] = override_context
    app.dependency_overrides[etl_router.get_etl_service] = lambda: FakeEtlService()

    from fastapi.testclient import TestClient

    client = TestClient(app)
    response = client.post(
        "/admin/etl/run",
        json={
            "dataset": "demographics",
            "country": "GH",
            "city": "Accra",
            "options": {"force": True},
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "QUEUED"
    assert body["payload"]["dataset"] == "demographics"


def test_admin_trigger_etl_requires_admin_role():
    app = create_app()

    class FakeEtlService:
        def trigger_adhoc_etl(self, *args, **kwargs):
            return {"status": "QUEUED", "payload": {}}

    def override_context():
        return CurrentRequestContext(user_id=uuid4(), tenant_id=uuid4(), role="USER")

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_request_context] = override_context
    app.dependency_overrides[etl_router.get_etl_service] = lambda: FakeEtlService()

    from fastapi.testclient import TestClient

    client = TestClient(app)
    response = client.post("/admin/etl/run", json={"dataset": "demographics"})
    assert response.status_code == 403
