"""Report jobs repository implementation."""

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.orm import Session

from models.reports import ReportJob


class ReportJobsRepository:
    """Data access for `report_jobs` and `report_sections` tables."""

    def create_pending_job(
        self,
        db_session: Session,
        tenant_id: UUID,
        city: str,
        country: str,
        business_type: str,
    ) -> ReportJob:
        now = datetime.now(timezone.utc)
        job = ReportJob(
            tenant_id=tenant_id,
            city=city,
            country=country,
            business_type=business_type,
            status="PENDING",
            pdf_url=None,
            error_message=None,
            created_at=now,
            updated_at=now,
        )
        db_session.add(job)
        db_session.flush()
        db_session.refresh(job)
        return job
