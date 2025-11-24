"""HTTP endpoint tests for admin user/tenant listing routes."""

from uuid import uuid4

from api.dependencies import CurrentRequestContext, get_current_request_context, get_db
from api.main import create_app
from api.routers import admin as admin_router
from api.schemas.core import TenantRead, UserRead


def override_db():
    """Provide a dummy DB session for dependency overrides."""

    class DummySession:
        """Stub SQLAlchemy session."""

    yield DummySession()


def test_admin_list_users_success():
    """`GET /admin/users` returns users for admin role."""
    app = create_app()
    expected_tenant_id = uuid4()

    class FakeAdminService:
        """Fake admin service asserting inputs."""

        def list_users(self, _db_session, email, role, tenant_id, _limit, _offset):
            """Return a canned users list."""
            assert email is None
            assert role is None
            assert tenant_id is None
            return [
                UserRead(
                    id=uuid4(),
                    tenant_id=expected_tenant_id,
                    email="admin@example.com",
                    name="Admin User",
                    role="ADMIN",
                )
            ]

        def list_tenants(self, _db_session, _name, _plan, _limit, _offset):
            """Return empty tenants list."""
            return []

    def override_context():
        """Provide a fake admin request context."""
        return CurrentRequestContext(
            user_id=uuid4(), tenant_id=expected_tenant_id, role="ADMIN"
        )

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_request_context] = override_context

    def override_admin_service():
        """Provide the fake admin service."""
        return FakeAdminService()

    app.dependency_overrides[admin_router.get_admin_service] = override_admin_service

    from fastapi.testclient import TestClient

    client = TestClient(app)
    response = client.get("/admin/users")

    assert response.status_code == 200
    assert len(response.json()["users"]) == 1


def test_admin_list_tenants_success():
    """`GET /admin/tenants` returns tenants for admin role."""
    app = create_app()
    expected_tenant_id = uuid4()

    class FakeAdminService:
        """Fake admin service returning canned tenants."""

        def list_users(self, _db_session, _email, _role, _tenant_id, _limit, _offset):
            """Return empty users list."""
            return []

        def list_tenants(self, _db_session, _name, _plan, _limit, _offset):
            """Return a canned tenants list."""
            return [
                TenantRead(
                    id=expected_tenant_id,
                    name="Acme",
                    plan="starter",
                )
            ]

    def override_context():
        """Provide a fake admin request context."""
        return CurrentRequestContext(
            user_id=uuid4(), tenant_id=expected_tenant_id, role="ADMIN"
        )

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_request_context] = override_context

    def override_admin_service():
        """Provide the fake admin service."""
        return FakeAdminService()

    app.dependency_overrides[admin_router.get_admin_service] = override_admin_service

    from fastapi.testclient import TestClient

    client = TestClient(app)
    response = client.get("/admin/tenants")

    assert response.status_code == 200
    assert len(response.json()["tenants"]) == 1


def test_admin_endpoints_missing_headers_returns_401():
    """Missing auth headers yields 401 on admin routes."""
    app = create_app()
    app.dependency_overrides[get_db] = override_db

    from fastapi.testclient import TestClient

    client = TestClient(app)
    response = client.get("/admin/users")

    assert response.status_code == 401
