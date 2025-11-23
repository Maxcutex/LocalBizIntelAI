from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from api.dependencies import CurrentRequestContext, get_current_request_context, get_db
from api.schemas.reports import (
    FeasibilityReportRequest,
    FeasibilityReportResponse,
    ReportGetResponse,
    ReportJobRead,
    ReportsListResponse,
)
from repositories.billing_repository import BillingRepository
from repositories.report_jobs_repository import ReportJobsRepository
from repositories.usage_repository import UsageRepository
from services.billing_service import BillingService
from services.dependencies import BillingServiceDependencies, ReportServiceDependencies
from services.pubsub_client import PubSubClient
from services.report_service import ReportService
from services.stripe_client import StripeClient

router = APIRouter()


def get_report_service() -> ReportService:
    billing_service = BillingService(
        BillingServiceDependencies(
            billing_repository=BillingRepository(),
            usage_repository=UsageRepository(),
            stripe_client=StripeClient(),
        )
    )
    return ReportService(
        ReportServiceDependencies(
            report_jobs_repository=ReportJobsRepository(),
            billing_service=billing_service,
            pubsub_client=PubSubClient(),
        )
    )


@router.post(
    "/feasibility",
    summary="Create feasibility report job",
)
def create_feasibility_report(
    request: FeasibilityReportRequest,
    db: Session = Depends(get_db),
    context: CurrentRequestContext = Depends(get_current_request_context),
    report_service: ReportService = Depends(get_report_service),
) -> FeasibilityReportResponse:
    """
    Create a new report job and enqueue processing.
    """
    result = report_service.create_feasibility_report(
        db_session=db,
        request=request,
        tenant_id=context.tenant_id,
        user_id=context.user_id,
    )
    return FeasibilityReportResponse.model_validate(result)


@router.get(
    "",
    summary="List report jobs for tenant",
)
def list_reports(
    db: Session = Depends(get_db),
    context: CurrentRequestContext = Depends(get_current_request_context),
    report_service: ReportService = Depends(get_report_service),
) -> ReportsListResponse:
    jobs = report_service.list_reports(db, context.tenant_id)
    return ReportsListResponse(
        reports=[ReportJobRead.model_validate(job) for job in jobs]
    )


@router.get(
    "/{report_id}",
    summary="Get report job status",
)
def get_report_status(
    report_id: UUID,
    db: Session = Depends(get_db),
    context: CurrentRequestContext = Depends(get_current_request_context),
    report_service: ReportService = Depends(get_report_service),
) -> ReportGetResponse:
    """
    Get current status and URL (when ready) for a report job.
    """
    job = report_service.get_report(db, report_id, context.tenant_id)
    return ReportGetResponse(report=ReportJobRead.model_validate(job))
