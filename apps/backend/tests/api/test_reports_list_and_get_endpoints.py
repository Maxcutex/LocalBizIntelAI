"""HTTP endpoint tests for listing and fetching reports."""

from uuid import UUID, uuid4

from api.dependencies import CurrentRequestContext, get_current_request_context, get_db
from api.main import create_app
from api.routers import reports as reports_router


def override_db():
    """Provide a dummy DB session for dependency overrides."""

    class DummySession:
        """Stub SQLAlchemy session."""

    yield DummySession()


class FakeJob:
    """Minimal report job fixture for HTTP response validation."""

    def __init__(self, job_id: UUID):
        """Create fixture with expected attributes."""
        self.id = job_id
        self.city = "Accra"
        self.country = "GH"
        self.business_type = "retail"
        self.status = "PENDING"
        self.pdf_url = None
        self.error_message = None
        self.created_at = None
        self.updated_at = None


def test_list_reports_success():
    """`GET /reports` returns jobs for tenant."""
    app = create_app()
    expected_tenant_id = uuid4()

    class FakeReportService:
        """Fake report service returning a canned list."""

        def list_reports(self, _db_session, tenant_id: UUID):
            """Return canned jobs list."""
            assert tenant_id == expected_tenant_id
            return [FakeJob(uuid4())]

    def override_context():
        """Provide a fake request context with tenant/user ids."""
        return CurrentRequestContext(user_id=uuid4(), tenant_id=expected_tenant_id)

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_request_context] = override_context

    def override_report_service():
        """Provide the fake report service."""
        return FakeReportService()

    app.dependency_overrides[reports_router.get_report_service] = (
        override_report_service
    )

    from fastapi.testclient import TestClient

    client = TestClient(app)
    response = client.get("/reports")

    assert response.status_code == 200
    data = response.json()
    assert "reports" in data
    assert len(data["reports"]) == 1


def test_get_report_success():
    """`GET /reports/{report_id}` returns report for tenant."""
    app = create_app()
    expected_tenant_id = uuid4()
    report_id = uuid4()

    class FakeReportService:
        """Fake report service returning a canned report."""

        def get_report(self, _db_session, requested_report_id: UUID, tenant_id: UUID):
            """Return the fixture report."""
            assert requested_report_id == report_id
            assert tenant_id == expected_tenant_id
            return FakeJob(report_id)

    def override_context():
        """Provide a fake request context with tenant/user ids."""
        return CurrentRequestContext(user_id=uuid4(), tenant_id=expected_tenant_id)

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_request_context] = override_context

    def override_report_service():
        """Provide the fake report service."""
        return FakeReportService()

    app.dependency_overrides[reports_router.get_report_service] = (
        override_report_service
    )

    from fastapi.testclient import TestClient

    client = TestClient(app)
    response = client.get(f"/reports/{report_id}")

    assert response.status_code == 200
    assert response.json()["report"]["id"] == str(report_id)


def test_get_report_not_found_returns_404():
    """Missing report yields 404."""
    app = create_app()
    expected_tenant_id = uuid4()

    class FakeReportService:
        """Fake report service raising 404."""

        def get_report(self, _db_session, _requested_report_id: UUID, _tenant_id: UUID):
            """Raise 404 for any lookup."""
            from fastapi import HTTPException, status

            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Report not found"
            )

    def override_context():
        """Provide a fake request context with tenant/user ids."""
        return CurrentRequestContext(user_id=uuid4(), tenant_id=expected_tenant_id)

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_request_context] = override_context

    def override_report_service():
        """Provide the fake report service."""
        return FakeReportService()

    app.dependency_overrides[reports_router.get_report_service] = (
        override_report_service
    )

    from fastapi.testclient import TestClient

    client = TestClient(app)
    response = client.get(f"/reports/{uuid4()}")

    assert response.status_code == 404


def test_list_reports_missing_headers_returns_401():
    """Missing auth headers yields 401."""
    app = create_app()
    app.dependency_overrides[get_db] = override_db

    from fastapi.testclient import TestClient

    client = TestClient(app)
    response = client.get("/reports")

    assert response.status_code == 401
