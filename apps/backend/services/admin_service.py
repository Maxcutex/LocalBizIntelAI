"""Admin operations service."""

from uuid import UUID

from sqlalchemy.orm import Session

from repositories.data_freshness_repository import DataFreshnessRepository
from repositories.report_jobs_repository import ReportJobsRepository
from repositories.tenant_repository import TenantRepository
from repositories.user_repository import UserRepository


class AdminService:
    """Admin-only operations, monitoring, and system management."""

    def __init__(
        self,
        user_repository: UserRepository | None = None,
        tenant_repository: TenantRepository | None = None,
        data_freshness_repository: DataFreshnessRepository | None = None,
        report_jobs_repository: ReportJobsRepository | None = None,
    ) -> None:
        self._user_repository = user_repository or UserRepository()
        self._tenant_repository = tenant_repository or TenantRepository()
        self._data_freshness_repository = (
            data_freshness_repository or DataFreshnessRepository()
        )
        self._report_jobs_repository = report_jobs_repository or ReportJobsRepository()

    def list_users(
        self,
        db_session: Session,
        email_contains: str | None,
        role: str | None,
        tenant_id: UUID | None,
        limit: int,
        offset: int,
    ) -> list:
        return self._user_repository.admin_list(
            db_session,
            email_contains=email_contains,
            role=role,
            tenant_id=tenant_id,
            limit=limit,
            offset=offset,
        )

    def list_tenants(
        self,
        db_session: Session,
        name_contains: str | None,
        plan: str | None,
        limit: int,
        offset: int,
    ) -> list:
        return self._tenant_repository.admin_list(
            db_session,
            name_contains=name_contains,
            plan=plan,
            limit=limit,
            offset=offset,
        )

    def list_dataset_freshness(self, db_session: Session) -> list:
        return self._data_freshness_repository.list_all(db_session)

    def list_report_jobs(
        self,
        db_session: Session,
        tenant_id: UUID | None,
        status: str | None,
        city: str | None,
        country: str | None,
        business_type: str | None,
        limit: int,
        offset: int,
    ) -> list:
        return self._report_jobs_repository.admin_list(
            db_session,
            tenant_id=tenant_id,
            status=status,
            city=city,
            country=country,
            business_type=business_type,
            limit=limit,
            offset=offset,
        )
