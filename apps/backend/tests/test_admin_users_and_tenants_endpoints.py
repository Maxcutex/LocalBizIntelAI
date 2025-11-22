from uuid import uuid4

from api.dependencies import CurrentRequestContext, get_current_request_context, get_db
from api.main import create_app
from api.routers import admin as admin_router
from api.schemas.core import TenantRead, UserRead


def override_db():
    class DummySession:
        pass

    yield DummySession()


def test_admin_list_users_success():
    app = create_app()
    expected_tenant_id = uuid4()

    class FakeAdminService:
        def list_users(self, db_session, email, role, tenant_id, limit, offset):
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

        def list_tenants(self, db_session, name, plan, limit, offset):
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
    response = client.get("/admin/users")

    assert response.status_code == 200
    assert len(response.json()["users"]) == 1


def test_admin_list_tenants_success():
    app = create_app()
    expected_tenant_id = uuid4()

    class FakeAdminService:
        def list_users(self, db_session, email, role, tenant_id, limit, offset):
            return []

        def list_tenants(self, db_session, name, plan, limit, offset):
            return [
                TenantRead(
                    id=expected_tenant_id,
                    name="Acme",
                    plan="starter",
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
    response = client.get("/admin/tenants")

    assert response.status_code == 200
    assert len(response.json()["tenants"]) == 1


def test_admin_endpoints_missing_headers_returns_401():
    app = create_app()
    app.dependency_overrides[get_db] = override_db

    from fastapi.testclient import TestClient

    client = TestClient(app)
    response = client.get("/admin/users")

    assert response.status_code == 401
