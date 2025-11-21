from fastapi import APIRouter, Depends, status

from services.tenant_service import TenantService

router = APIRouter()


def get_tenant_service() -> TenantService:
    return TenantService()


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
