"""Tenant repository implementation."""

from uuid import UUID

from sqlalchemy.orm import Session

from models.core import Tenant


class TenantRepository:
    """Data access for `tenants` table."""

    def get_by_id(self, db_session: Session, tenant_id: UUID) -> Tenant | None:
        return db_session.get(Tenant, tenant_id)
