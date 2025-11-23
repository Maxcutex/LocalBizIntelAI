"""Insight-generation routes (market summary and opportunity finder)."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from api.config import get_settings
from api.dependencies import CurrentRequestContext, get_current_request_context, get_db
from api.schemas.insights import (
    MarketSummaryRequest,
    MarketSummaryResponse,
    OpportunitiesRequest,
    OpportunitiesResponse,
)
from repositories.demographics_repository import DemographicsRepository
from repositories.labour_stats_repository import LabourStatsRepository
from repositories.opportunity_scores_repository import OpportunityScoresRepository
from repositories.spending_repository import SpendingRepository
from services.ai_engine_client import AiEngineClient
from services.dependencies import InsightServiceDependencies
from services.insight_service import InsightService

router = APIRouter()


def get_insight_service() -> InsightService:
    """Construct an `InsightService` with concrete repositories and AI client."""
    ai_engine_client = AiEngineClient(get_settings())
    return InsightService(
        InsightServiceDependencies(
            demographics_repository=DemographicsRepository(),
            spending_repository=SpendingRepository(),
            labour_stats_repository=LabourStatsRepository(),
            opportunity_scores_repository=OpportunityScoresRepository(),
            ai_engine_client=ai_engine_client,
        )
    )


@router.post(
    "/market-summary",
    summary="Generate market summary insight",
)
def generate_market_summary(
    request: MarketSummaryRequest,
    db: Session = Depends(get_db),
    context: CurrentRequestContext = Depends(get_current_request_context),
    insight_service: InsightService = Depends(get_insight_service),
) -> MarketSummaryResponse:
    """
    Orchestrate market data + AI-engine to generate a narrative summary.

    Example request:

        POST /insights/market-summary
        {
          "city": "Toronto",
          "country": "CA",
          "regions": ["toronto-downtown"]
        }
    """
    result = insight_service.generate_market_summary(
        db_session=db,
        city=request.city,
        country=request.country,
        tenant_id=context.tenant_id,
        regions=request.regions,
    )
    return MarketSummaryResponse.model_validate(result)


@router.post(
    "/opportunities",
    summary="Generate opportunity insights",
)
def generate_opportunities(
    request: OpportunitiesRequest,
    db: Session = Depends(get_db),
    context: CurrentRequestContext = Depends(get_current_request_context),
    insight_service: InsightService = Depends(get_insight_service),
) -> OpportunitiesResponse:
    """
    Return ranked opportunities with AI explanations.

    Example request:

        POST /insights/opportunities
        {
          "city": "Toronto",
          "country": "CA",
          "business_type": "restaurant",
          "constraints": { "min_composite_score": 0.6 }
        }
    """
    result = insight_service.find_opportunities(
        db_session=db,
        city=request.city,
        business_type=request.business_type,
        constraints=request.constraints,
        country=request.country,
        tenant_id=context.tenant_id,
    )
    return OpportunitiesResponse.model_validate(result)
