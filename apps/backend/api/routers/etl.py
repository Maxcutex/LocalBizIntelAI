"""ETL orchestration routes for triggering ingestion runs (admin-only)."""

from fastapi import APIRouter, Depends, HTTPException
from fastapi import status as http_status
from sqlalchemy.orm import Session

from api.dependencies import get_current_request_context, get_db
from api.schemas.etl import EtlRunRequest, EtlRunResponse
from services.dependencies import EtlOrchestrationServiceDependencies
from services.etl_orchestration_service import ETLOrchestrationService
from services.pubsub_client import PubSubClient

router = APIRouter()


def get_etl_service() -> ETLOrchestrationService:
    """Construct an `ETLOrchestrationService` with a PubSub client."""
    return ETLOrchestrationService(
        EtlOrchestrationServiceDependencies(pubsub_client=PubSubClient())
    )


@router.post(
    "/run",
    summary="Trigger ETL run",
)
def trigger_etl_run(
    request: EtlRunRequest,
    db: Session = Depends(get_db),
    context=Depends(get_current_request_context),
    etl_service: ETLOrchestrationService = Depends(get_etl_service),
) -> EtlRunResponse:
    """
    Admin endpoint to trigger an ETL workflow.

    Example request:

        POST /etl/run
        {
          "dataset": "demographics",
          "country": "CA",
          "city": "Toronto",
          "options": { "full_refresh": true }
        }
    """
    if context.role != "ADMIN":
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="Admin role required",
        )

    result = etl_service.trigger_adhoc_etl(
        db_session=db,
        dataset=request.dataset,
        country=request.country,
        city=request.city,
        options=request.options,
        triggered_by_user_id=context.user_id,
        triggered_by_tenant_id=context.tenant_id,
    )
    return EtlRunResponse.model_validate(result)
