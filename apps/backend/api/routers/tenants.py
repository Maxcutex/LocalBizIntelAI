from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from api.dependencies import CurrentRequestContext, get_current_request_context, get_db
from repositories.tenant_repository import TenantRepository
from services.dependencies import TenantServiceDependencies
from services.tenant_service import TenantService

router = APIRouter()


def get_tenant_service() -> TenantService:
    return TenantService(
        TenantServiceDependencies(tenant_repository=TenantRepository())
    )


@router.get(
    "/",
    summary="List tenants",
    status_code=status.HTTP_501_NOT_IMPLEMENTED,
)
def list_tenants(tenant_service: TenantService = Depends(get_tenant_service)) -> dict:
    """
    List tenants accessible to the current user.
    """
    return {"detail": "Not implemented"}


@router.post(
    "/",
    summary="Create tenant",
    status_code=status.HTTP_501_NOT_IMPLEMENTED,
)
def create_tenant(tenant_service: TenantService = Depends(get_tenant_service)) -> dict:
    """
    Create a new tenant/workspace.
    """
    return {"detail": "Not implemented"}


@router.get(
    "/current",
    summary="Get current tenant",
)
def get_current_tenant(
    db: Session = Depends(get_db),
    context: CurrentRequestContext = Depends(get_current_request_context),
    tenant_service: TenantService = Depends(get_tenant_service),
) -> dict:
    """
    Returns the current tenant based on auth context.
    """
    return tenant_service.get_current_tenant(db, context.tenant_id).model_dump()
