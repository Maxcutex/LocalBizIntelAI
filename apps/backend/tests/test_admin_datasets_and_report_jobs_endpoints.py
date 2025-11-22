from datetime import datetime, timezone
from uuid import uuid4

from api.dependencies import CurrentRequestContext, get_current_request_context, get_db
from api.main import create_app
from api.routers import admin as admin_router
from api.schemas.admin import DataFreshnessRead
from api.schemas.reports import ReportJobRead


def override_db():
    class DummySession:
        pass

    yield DummySession()


def test_admin_list_datasets_success():
    app = create_app()
    expected_tenant_id = uuid4()

    class FakeAdminService:
        def list_dataset_freshness(self, db_session):
            return [
                DataFreshnessRead(
                    id=uuid4(),
                    dataset_name="demographics",
                    last_run=datetime(2025, 1, 1, tzinfo=timezone.utc),
                    row_count=123,
                    status="OK",
                )
            ]

        def list_report_jobs(
            self,
            db_session,
            tenant_id,
            status,
            city,
            country,
            business_type,
            limit,
            offset,
        ):
            return []

    def override_context():
        return CurrentRequestContext(
            user_id=uuid4(), tenant_id=expected_tenant_id, role="ADMIN"
        )

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_request_context] = override_context
    app.dependency_overrides[admin_router.get_admin_service] = (
        lambda: FakeAdminService()
    )

    from fastapi.testclient import TestClient

    client = TestClient(app)
    response = client.get("/admin/datasets")

    assert response.status_code == 200
    body = response.json()
    assert len(body["datasets"]) == 1
    assert body["datasets"][0]["dataset_name"] == "demographics"


def test_admin_list_report_jobs_success_and_filters_passed():
    app = create_app()
    expected_tenant_id = uuid4()
    requested_tenant_id = uuid4()

    class FakeAdminService:
        def list_dataset_freshness(self, db_session):
            return []

        def list_report_jobs(
            self,
            db_session,
            tenant_id,
            status,
            city,
            country,
            business_type,
            limit,
            offset,
        ):
            assert tenant_id == requested_tenant_id
            assert status == "COMPLETED"
            assert city == "Accra"
            assert country is None
            assert business_type == "restaurant"
            assert limit == 2
            assert offset == 1
            return [
                ReportJobRead(
                    id=uuid4(),
                    city="Accra",
                    country="GH",
                    business_type="restaurant",
                    status="COMPLETED",
                    pdf_url="https://example.com/report.pdf",
                    error_message=None,
                    created_at=None,
                    updated_at=None,
                )
            ]

    def override_context():
        return CurrentRequestContext(
            user_id=uuid4(), tenant_id=expected_tenant_id, role="ADMIN"
        )

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_request_context] = override_context
    app.dependency_overrides[admin_router.get_admin_service] = (
        lambda: FakeAdminService()
    )

    from fastapi.testclient import TestClient

    client = TestClient(app)
    response = client.get(
        "/admin/jobs/reports",
        params={
            "tenant_id": str(requested_tenant_id),
            "status": "COMPLETED",
            "city": "Accra",
            "business_type": "restaurant",
            "limit": 2,
            "offset": 1,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert len(body["report_jobs"]) == 1
    assert body["report_jobs"][0]["status"] == "COMPLETED"


def test_admin_datasets_requires_admin_role():
    app = create_app()
    expected_tenant_id = uuid4()

    class FakeAdminService:
        def list_dataset_freshness(self, db_session):
            return []

        def list_report_jobs(
            self,
            db_session,
            tenant_id,
            status,
            city,
            country,
            business_type,
            limit,
            offset,
        ):
            return []

    def override_context():
        return CurrentRequestContext(
            user_id=uuid4(), tenant_id=expected_tenant_id, role="USER"
        )

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_request_context] = override_context
    app.dependency_overrides[admin_router.get_admin_service] = (
        lambda: FakeAdminService()
    )

    from fastapi.testclient import TestClient

    client = TestClient(app)
    response = client.get("/admin/datasets")

    assert response.status_code == 403
