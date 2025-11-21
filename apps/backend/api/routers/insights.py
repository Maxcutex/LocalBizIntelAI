from fastapi import APIRouter, Depends, status

from services.insight_service import InsightService

router = APIRouter()


def get_insight_service() -> InsightService:
    return InsightService()


@router.post(
    "/market-summary",
    summary="Generate market summary insight",
    status_code=status.HTTP_501_NOT_IMPLEMENTED,
)
def generate_market_summary(
    insight_service: InsightService = Depends(get_insight_service),
) -> dict:
    """
    Orchestrate market data + AI-engine to generate a narrative summary.
    """
    return {"detail": "Not implemented"}


@router.post(
    "/opportunities",
    summary="Generate opportunity insights",
    status_code=status.HTTP_501_NOT_IMPLEMENTED,
)
def generate_opportunities(
    insight_service: InsightService = Depends(get_insight_service),
) -> dict:
    """
    Return ranked opportunities with AI explanations.
    """
    return {"detail": "Not implemented"}
