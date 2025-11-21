from fastapi import APIRouter, Depends, status

from services.admin_service import AdminService

router = APIRouter()


def get_admin_service() -> AdminService:
    return AdminService()


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
