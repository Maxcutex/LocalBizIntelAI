from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from api.dependencies import get_current_request_context, get_db
from api.schemas.admin import AdminTenantsListResponse, AdminUsersListResponse
from api.schemas.core import TenantRead, UserRead
from services.admin_service import AdminService

router = APIRouter()


def get_admin_service() -> AdminService:
    return AdminService()


@router.get(
    "/users",
    summary="List users (admin)",
)
def list_users(
    email: str | None = Query(default=None),
    role: str | None = Query(default=None),
    tenant_id: UUID | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    _context=Depends(get_current_request_context),
    admin_service: AdminService = Depends(get_admin_service),
) -> AdminUsersListResponse:
    users = admin_service.list_users(db, email, role, tenant_id, limit, offset)
    return AdminUsersListResponse(
        users=[UserRead.model_validate(user) for user in users]
    )


@router.get(
    "/tenants",
    summary="List tenants (admin)",
)
def list_tenants(
    name: str | None = Query(default=None),
    plan: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    _context=Depends(get_current_request_context),
    admin_service: AdminService = Depends(get_admin_service),
) -> AdminTenantsListResponse:
    tenants = admin_service.list_tenants(db, name, plan, limit, offset)
    return AdminTenantsListResponse(
        tenants=[TenantRead.model_validate(tenant) for tenant in tenants]
    )


@router.get(
    "/system/health",
    summary="Admin system health",
    status_code=status.HTTP_501_NOT_IMPLEMENTED,
)
def system_health(admin_service: AdminService = Depends(get_admin_service)) -> dict:
    """
    Return internal system health and monitoring data.
    """
    return {"detail": "Not implemented"}
