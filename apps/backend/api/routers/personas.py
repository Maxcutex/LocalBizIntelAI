from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from api.config import get_settings
from api.dependencies import CurrentRequestContext, get_current_request_context, get_db
from api.schemas.personas import PersonaGenerateRequest, PersonaGenerateResponse
from repositories.demographics_repository import DemographicsRepository
from repositories.labour_stats_repository import LabourStatsRepository
from repositories.spending_repository import SpendingRepository
from services.ai_engine_client import AiEngineClient
from services.dependencies import PersonaServiceDependencies
from services.persona_service import PersonaService

router = APIRouter()


def get_persona_service() -> PersonaService:
    ai_engine_client = AiEngineClient(get_settings())
    return PersonaService(
        PersonaServiceDependencies(
            demographics_repository=DemographicsRepository(),
            spending_repository=SpendingRepository(),
            labour_stats_repository=LabourStatsRepository(),
            ai_engine_client=ai_engine_client,
        )
    )


@router.post(
    "/generate",
    summary="Generate personas",
)
def generate_personas(
    request: PersonaGenerateRequest,
    db: Session = Depends(get_db),
    context: CurrentRequestContext = Depends(get_current_request_context),
    persona_service: PersonaService = Depends(get_persona_service),
) -> PersonaGenerateResponse:
    """
    Generate personas for a market/area using demographics + AI-engine.
    """
    result = persona_service.generate_personas(
        db_session=db,
        city=request.city,
        country=request.country,
        geo_ids=request.geo_ids,
        business_type=request.business_type,
        tenant_id=context.tenant_id,
    )
    return PersonaGenerateResponse.model_validate(result)
