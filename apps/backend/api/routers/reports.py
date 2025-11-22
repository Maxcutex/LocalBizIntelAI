from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from api.dependencies import CurrentRequestContext, get_current_request_context, get_db
from api.schemas.reports import FeasibilityReportRequest, FeasibilityReportResponse
from services.report_service import ReportService

router = APIRouter()


def get_report_service() -> ReportService:
    return ReportService()


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
    "/{report_id}",
    summary="Get report job status",
    status_code=status.HTTP_501_NOT_IMPLEMENTED,
)
def get_report_status(
    report_id: str, report_service: ReportService = Depends(get_report_service)
) -> dict:
    """
    Get current status and URL (when ready) for a report job.
    """
    return {"detail": "Not implemented"}
