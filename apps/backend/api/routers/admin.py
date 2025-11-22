from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi import status as http_status
from sqlalchemy.orm import Session

from api.dependencies import get_current_request_context, get_db
from api.schemas.admin import (
    AdminDatasetsListResponse,
    AdminReportJobsListResponse,
    AdminTenantsListResponse,
    AdminUsersListResponse,
    DataFreshnessRead,
)
from api.schemas.core import TenantRead, UserRead
from api.schemas.reports import ReportJobRead
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
    context=Depends(get_current_request_context),
    admin_service: AdminService = Depends(get_admin_service),
) -> AdminUsersListResponse:
    if context.role != "ADMIN":
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="Admin role required",
        )
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
    context=Depends(get_current_request_context),
    admin_service: AdminService = Depends(get_admin_service),
) -> AdminTenantsListResponse:
    if context.role != "ADMIN":
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="Admin role required",
        )
    tenants = admin_service.list_tenants(db, name, plan, limit, offset)
    return AdminTenantsListResponse(
        tenants=[TenantRead.model_validate(tenant) for tenant in tenants]
    )


@router.get(
    "/datasets",
    summary="List dataset freshness (admin)",
)
def list_datasets(
    db: Session = Depends(get_db),
    context=Depends(get_current_request_context),
    admin_service: AdminService = Depends(get_admin_service),
) -> AdminDatasetsListResponse:
    if context.role != "ADMIN":
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="Admin role required",
        )

    datasets = admin_service.list_dataset_freshness(db)
    return AdminDatasetsListResponse(
        datasets=[DataFreshnessRead.model_validate(ds) for ds in datasets]
    )


@router.get(
    "/jobs/reports",
    summary="List report jobs (admin)",
)
def list_report_jobs(
    tenant_id: UUID | None = Query(default=None),
    status: str | None = Query(default=None),
    city: str | None = Query(default=None),
    country: str | None = Query(default=None),
    business_type: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    context=Depends(get_current_request_context),
    admin_service: AdminService = Depends(get_admin_service),
) -> AdminReportJobsListResponse:
    if context.role != "ADMIN":
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="Admin role required",
        )

    jobs = admin_service.list_report_jobs(
        db,
        tenant_id=tenant_id,
        status=status,
        city=city,
        country=country,
        business_type=business_type,
        limit=limit,
        offset=offset,
    )
    return AdminReportJobsListResponse(
        report_jobs=[ReportJobRead.model_validate(job) for job in jobs]
    )


@router.get(
    "/system/health",
    summary="Admin system health",
    status_code=http_status.HTTP_501_NOT_IMPLEMENTED,
)
def system_health(admin_service: AdminService = Depends(get_admin_service)) -> dict:
    """
    Return internal system health and monitoring data.
    """
    return {"detail": "Not implemented"}
