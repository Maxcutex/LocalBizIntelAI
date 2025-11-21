from fastapi import APIRouter, Depends, status

from services.report_service import ReportService

router = APIRouter()


def get_report_service() -> ReportService:
    return ReportService()


@router.post(
    "/feasibility",
    summary="Create feasibility report job",
    status_code=status.HTTP_501_NOT_IMPLEMENTED,
)
def create_feasibility_report(
    report_service: ReportService = Depends(get_report_service),
) -> dict:
    """
    Create a new report job and enqueue processing.
    """
    return {"detail": "Not implemented"}


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
