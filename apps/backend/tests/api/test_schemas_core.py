"""Unit tests for core Pydantic schemas."""

from datetime import datetime, timezone
from uuid import uuid4

from api.schemas.core import TenantRead, UserRead


def test_tenant_read_from_attributes():
    """TenantRead validates from attribute-based objects."""
    tenant_id = uuid4()
    now = datetime.now(timezone.utc)

    class Obj:
        """Attribute fixture matching TenantRead fields."""

        def __init__(self):
            """Populate fixture fields."""
            self.id = tenant_id
            self.name = "Acme Inc"
            self.plan = "starter"
            self.created_at = now
            self.updated_at = now

    tenant = TenantRead.model_validate(Obj())

    assert tenant.id == tenant_id
    assert tenant.name == "Acme Inc"
    assert tenant.plan == "starter"
    assert tenant.created_at == now
    assert tenant.updated_at == now


def test_user_read_from_attributes():
    """UserRead validates from attribute-based objects."""
    user_id = uuid4()
    tenant_id = uuid4()
    now = datetime.now(timezone.utc)

    class Obj:
        """Attribute fixture matching UserRead fields."""

        def __init__(self):
            """Populate fixture fields."""
            self.id = user_id
            self.tenant_id = tenant_id
            self.email = "test@example.com"
            self.name = "Test User"
            self.role = "USER"
            self.created_at = now

    user = UserRead.model_validate(Obj())

    assert user.id == user_id
    assert user.tenant_id == tenant_id
    assert user.email == "test@example.com"
    assert user.name == "Test User"
    assert user.role == "USER"
    assert user.created_at == now
