from uuid import uuid4

from api.config import get_settings
from api.dependencies import get_current_request_context
from api.security.jwt import create_access_token


def test_bearer_token_builds_context():
    settings = get_settings()
    user_id = uuid4()
    tenant_id = uuid4()
    token = create_access_token(
        user_id=user_id,
        tenant_id=tenant_id,
        role="ADMIN",
        settings=settings,
    )

    context = get_current_request_context(
        authorization=f"Bearer {token}",
        x_user_id=None,
        x_tenant_id=None,
    )

    assert context.user_id == user_id
    assert context.tenant_id == tenant_id
    assert context.role == "ADMIN"


def test_bearer_token_invalid_raises_401():
    import pytest
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc_info:
        get_current_request_context(
            authorization="Bearer invalid.token",
            x_user_id=None,
            x_tenant_id=None,
        )

    assert exc_info.value.status_code == 401
