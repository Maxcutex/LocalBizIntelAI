from datetime import datetime, timezone
from uuid import UUID, uuid4

import pytest
from fastapi import HTTPException, status

from api.dependencies import get_current_request_context, get_db
from api.main import create_app
from api.routers import me as me_router
from api.routers import tenants as tenants_router
from api.schemas.core import TenantRead, UserRead


@pytest.fixture()
def app():
    return create_app()


@pytest.fixture()
def client(app):
    from fastapi.testclient import TestClient

    return TestClient(app)


def override_db():
    class DummySession:
        pass

    yield DummySession()


def test_get_me_success(app, client):
    user_id = uuid4()
    tenant_id = uuid4()
    now = datetime.now(timezone.utc)

    class FakeAuthService:
        def get_current_user_profile(self, db_session, requested_user_id: UUID):
            assert requested_user_id == user_id
            return {
                "user": UserRead(
                    id=user_id,
                    tenant_id=tenant_id,
                    email="test@example.com",
                    name="Test User",
                    role="USER",
                    created_at=now,
                ),
                "tenant": TenantRead(
                    id=tenant_id,
                    name="Acme",
                    plan="starter",
                    created_at=now,
                    updated_at=now,
                ),
            }

    def override_context():
        from api.dependencies import CurrentRequestContext

        return CurrentRequestContext(user_id=user_id, tenant_id=tenant_id)

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_request_context] = override_context
    app.dependency_overrides[me_router.get_auth_service] = lambda: FakeAuthService()

    response = client.get("/me")

    assert response.status_code == 200
    payload = response.json()
    assert payload["user"]["id"] == str(user_id)
    assert payload["tenant"]["id"] == str(tenant_id)


def test_get_me_missing_headers_returns_401(app, client):
    app.dependency_overrides[get_db] = override_db

    response = client.get("/me")

    assert response.status_code == 401


def test_get_me_invalid_headers_returns_400(app, client):
    app.dependency_overrides[get_db] = override_db

    response = client.get(
        "/me",
        headers={
            "X-User-Id": "not-a-uuid",
            "X-Tenant-Id": "also-not-a-uuid",
        },
    )

    assert response.status_code == 400


def test_get_me_user_not_found_returns_404(app, client):
    user_id = uuid4()
    tenant_id = uuid4()

    class FakeAuthService:
        def get_current_user_profile(self, db_session, requested_user_id: UUID):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

    def override_context():
        from api.dependencies import CurrentRequestContext

        return CurrentRequestContext(user_id=user_id, tenant_id=tenant_id)

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_request_context] = override_context
    app.dependency_overrides[me_router.get_auth_service] = lambda: FakeAuthService()

    response = client.get("/me")

    assert response.status_code == 404


def test_get_current_tenant_success(app, client):
    user_id = uuid4()
    tenant_id = uuid4()
    now = datetime.now(timezone.utc)

    class FakeTenantService:
        def get_current_tenant(self, db_session, requested_tenant_id: UUID):
            assert requested_tenant_id == tenant_id
            return TenantRead(
                id=tenant_id,
                name="Acme",
                plan="starter",
                created_at=now,
                updated_at=now,
            )

    def override_context():
        from api.dependencies import CurrentRequestContext

        return CurrentRequestContext(user_id=user_id, tenant_id=tenant_id)

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_request_context] = override_context
    app.dependency_overrides[tenants_router.get_tenant_service] = (
        lambda: FakeTenantService()
    )

    response = client.get("/tenants/current")

    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == str(tenant_id)
    assert payload["name"] == "Acme"


def test_get_current_tenant_missing_headers_returns_401(app, client):
    app.dependency_overrides[get_db] = override_db

    response = client.get("/tenants/current")

    assert response.status_code == 401


def test_get_current_tenant_invalid_headers_returns_400(app, client):
    app.dependency_overrides[get_db] = override_db

    response = client.get(
        "/tenants/current",
        headers={
            "X-User-Id": "not-a-uuid",
            "X-Tenant-Id": "also-not-a-uuid",
        },
    )

    assert response.status_code == 400


def test_get_current_tenant_not_found_returns_404(app, client):
    user_id = uuid4()
    tenant_id = uuid4()

    class FakeTenantService:
        def get_current_tenant(self, db_session, requested_tenant_id: UUID):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found"
            )

    def override_context():
        from api.dependencies import CurrentRequestContext

        return CurrentRequestContext(user_id=user_id, tenant_id=tenant_id)

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_request_context] = override_context
    app.dependency_overrides[tenants_router.get_tenant_service] = (
        lambda: FakeTenantService()
    )

    response = client.get("/tenants/current")

    assert response.status_code == 404
