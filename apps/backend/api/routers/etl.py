from fastapi import APIRouter, Depends, status

from services.etl_orchestration_service import ETLOrchestrationService

router = APIRouter()


def get_etl_service() -> ETLOrchestrationService:
    return ETLOrchestrationService()


@router.post(
    "/run",
    summary="Trigger ETL run",
    status_code=status.HTTP_501_NOT_IMPLEMENTED,
)
def trigger_etl_run(
    etl_service: ETLOrchestrationService = Depends(get_etl_service),
) -> dict:
    """
    Admin endpoint to trigger an ETL workflow.
    """
    return {"detail": "Not implemented"}
