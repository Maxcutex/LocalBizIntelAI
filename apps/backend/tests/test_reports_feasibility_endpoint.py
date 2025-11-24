"""HTTP endpoint tests for feasibility report creation."""

from uuid import UUID, uuid4

from api.dependencies import CurrentRequestContext, get_current_request_context, get_db
from api.main import create_app
from api.routers import reports as reports_router


def override_db():
    """Provide a dummy DB session for dependency overrides."""

    class DummySession:
        """Stub SQLAlchemy session."""

    yield DummySession()


def test_create_feasibility_report_success():
    """`POST /reports/feasibility` enqueues a job with valid auth."""
    app = create_app()
    expected_tenant_id = uuid4()
    expected_user_id = uuid4()

    class FakeReportService:
        """Fake report service asserting input and returning canned job."""

        def create_feasibility_report(
            self,
            _db_session,
            request,
            tenant_id: UUID,
            user_id: UUID,
        ):
            """Return deterministic job response."""
            assert request.city == "Accra"
            assert request.country == "GH"
            assert request.business_type == "retail"
            assert tenant_id == expected_tenant_id
            assert user_id == expected_user_id
            return {"job_id": "job-123", "status": "PENDING"}

    def override_context():
        """Provide a fake request context with tenant/user ids."""
        return CurrentRequestContext(
            user_id=expected_user_id, tenant_id=expected_tenant_id
        )

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_request_context] = override_context

    def override_report_service():
        """Provide a fake report service."""
        return FakeReportService()

    app.dependency_overrides[reports_router.get_report_service] = (
        override_report_service
    )

    from fastapi.testclient import TestClient

    client = TestClient(app)
    response = client.post(
        "/reports/feasibility",
        json={"city": "Accra", "country": "GH", "business_type": "retail"},
    )

    assert response.status_code == 200
    assert response.json() == {"job_id": "job-123", "status": "PENDING"}


def test_create_feasibility_report_missing_headers_returns_401():
    """Missing auth headers yields 401."""
    app = create_app()
    app.dependency_overrides[get_db] = override_db

    from fastapi.testclient import TestClient

    client = TestClient(app)
    response = client.post(
        "/reports/feasibility",
        json={"city": "Accra", "country": "GH", "business_type": "retail"},
    )

    assert response.status_code == 401
