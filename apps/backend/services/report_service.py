"""Report management service."""

from typing import Any
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from api.schemas.reports import FeasibilityReportRequest
from repositories.report_jobs_repository import ReportJobsRepository
from services.billing_service import BillingService
from services.pubsub_client import PubSubClient


class ReportService:
    """Creates and tracks feasibility report jobs and PDF generation."""

    def __init__(
        self,
        report_jobs_repository: ReportJobsRepository | None = None,
        billing_service: BillingService | None = None,
        pubsub_client: PubSubClient | None = None,
    ) -> None:
        self._report_jobs_repository = report_jobs_repository or ReportJobsRepository()
        self._billing_service = billing_service or BillingService()
        self._pubsub_client = pubsub_client or PubSubClient()

    def create_feasibility_report(
        self,
        db_session: Session,
        request: FeasibilityReportRequest,
        tenant_id: UUID,
        user_id: UUID,
    ) -> dict[str, Any]:
        quota_ok = self._billing_service.check_report_quota(db_session, tenant_id)
        if not quota_ok:
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail="Report quota exceeded",
            )

        job = self._report_jobs_repository.create_pending_job(
            db_session,
            tenant_id=tenant_id,
            city=request.city,
            country=request.country,
            business_type=request.business_type,
        )

        self._pubsub_client.publish_report_job(
            topic="report-jobs",
            message={
                "report_job_id": str(job.id),
                "tenant_id": str(tenant_id),
                "user_id": str(user_id),
                "city": request.city,
                "country": request.country,
                "business_type": request.business_type,
            },
        )

        return {"job_id": str(job.id), "status": job.status}

    def list_reports(self, db_session: Session, tenant_id: UUID) -> list[Any]:
        jobs = self._report_jobs_repository.list_by_tenant(db_session, tenant_id)
        return jobs

    def get_report(self, db_session: Session, report_id: UUID, tenant_id: UUID) -> Any:
        job = self._report_jobs_repository.get_for_tenant(
            db_session, report_id, tenant_id
        )
        if job is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Report not found",
            )
        return job
