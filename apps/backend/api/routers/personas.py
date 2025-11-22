from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from api.dependencies import CurrentRequestContext, get_current_request_context, get_db
from api.schemas.personas import PersonaGenerateRequest, PersonaGenerateResponse
from services.persona_service import PersonaService

router = APIRouter()


def get_persona_service() -> PersonaService:
    return PersonaService()


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
