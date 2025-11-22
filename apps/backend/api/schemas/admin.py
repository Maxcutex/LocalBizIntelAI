"""Pydantic schemas for admin endpoints."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel
from pydantic.config import ConfigDict

from api.schemas.core import TenantRead, UserRead
from api.schemas.reports import ReportJobRead


class AdminUsersListResponse(BaseModel):
    users: list[UserRead]


class AdminTenantsListResponse(BaseModel):
    tenants: list[TenantRead]


class DataFreshnessRead(BaseModel):
    id: UUID
    dataset_name: str
    last_run: datetime | None = None
    row_count: int | None = None
    status: str | None = None

    model_config = ConfigDict(from_attributes=True)


class AdminDatasetsListResponse(BaseModel):
    datasets: list[DataFreshnessRead]


class AdminReportJobsListResponse(BaseModel):
    report_jobs: list[ReportJobRead]
