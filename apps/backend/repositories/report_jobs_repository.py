"""Report jobs repository implementation."""

from datetime import datetime, timezone
from typing import cast
from uuid import UUID

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from models.reports import ReportJob


class ReportJobsRepository:
    """Data access for `report_jobs` and `report_sections` tables."""

    def list_by_tenant(self, db_session: Session, tenant_id: UUID) -> list[ReportJob]:
        query: Select = (
            select(ReportJob)
            .where(ReportJob.tenant_id == tenant_id)
            .order_by(ReportJob.created_at.desc())
        )
        result = db_session.execute(query).scalars().all()
        return cast(list[ReportJob], list(result))

    def get_for_tenant(
        self, db_session: Session, report_id: UUID, tenant_id: UUID
    ) -> ReportJob | None:
        query: Select = select(ReportJob).where(
            ReportJob.id == report_id, ReportJob.tenant_id == tenant_id
        )
        return db_session.execute(query).scalars().first()

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
