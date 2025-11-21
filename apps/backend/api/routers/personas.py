from fastapi import APIRouter, Depends, status

from services.persona_service import PersonaService

router = APIRouter()


def get_persona_service() -> PersonaService:
    return PersonaService()


@router.post(
    "/generate",
    summary="Generate personas",
    status_code=status.HTTP_501_NOT_IMPLEMENTED,
)
def generate_personas(
    persona_service: PersonaService = Depends(get_persona_service),
) -> dict:
    """
    Generate personas for a market/area using demographics + AI-engine.
    """
    return {"detail": "Not implemented"}
