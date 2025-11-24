"""Tenant repository implementation."""

from typing import cast
from uuid import UUID

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from models.core import Tenant


class TenantRepository:
    """Data access for `tenants` table."""

    def get_by_id(self, db_session: Session, tenant_id: UUID) -> Tenant | None:
        """Get a tenant by id, returning None if it does not exist."""
        return db_session.get(Tenant, tenant_id)

    def admin_list(
        self,
        db_session: Session,
        name_contains: str | None = None,
        plan: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Tenant]:
        """
        Admin listing of tenants with optional filters and pagination.

        Args:
            name_contains: Optional substring match for tenant name.
            plan: Optional plan filter.
            limit: Max number of results.
            offset: Pagination offset.
        """
        query: Select = select(Tenant)
        if plan:
            query = query.where(Tenant.plan == plan)
        if name_contains:
            query = query.where(Tenant.name.ilike(f"%{name_contains}%"))
        query = query.order_by(Tenant.created_at.desc()).limit(limit).offset(offset)
        result = db_session.execute(query).scalars().all()
        return cast(list[Tenant], list(result))
