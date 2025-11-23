"""Tenant/workspace management service."""

from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from api.schemas.core import TenantRead
from repositories.tenant_repository import TenantRepository


class TenantService:
    """Manages tenants, organizations, memberships, and plan context."""

    def __init__(self, tenant_repository: TenantRepository) -> None:
        self._tenant_repository = tenant_repository

    def get_current_tenant(self, db_session: Session, tenant_id: UUID) -> TenantRead:
        tenant = self._tenant_repository.get_by_id(db_session, tenant_id)
        if tenant is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tenant not found",
            )

        return TenantRead.model_validate(tenant)
