from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from api.dependencies import CurrentRequestContext, get_current_request_context, get_db
from repositories.business_density_repository import BusinessDensityRepository
from repositories.demographics_repository import DemographicsRepository
from repositories.labour_stats_repository import LabourStatsRepository
from repositories.spending_repository import SpendingRepository
from services.dependencies import MarketServiceDependencies
from services.market_service import MarketService

router = APIRouter()


def get_market_service() -> MarketService:
    return MarketService(
        MarketServiceDependencies(
            demographics_repository=DemographicsRepository(),
            business_density_repository=BusinessDensityRepository(),
            spending_repository=SpendingRepository(),
            labour_stats_repository=LabourStatsRepository(),
        )
    )


@router.get(
    "/cities",
    summary="List cities with market data",
)
def list_cities(
    country: str | None = Query(default=None),
    db: Session = Depends(get_db),
    market_service: MarketService = Depends(get_market_service),
) -> dict:
    """
    Return distinct cities where market data exists (optionally filtered by country).
    """
    cities = market_service.list_cities(db, country)
    return {"cities": cities}


@router.get(
    "/{city}/overview",
    summary="Get market overview",
)
def get_market_overview(
    city: str,
    country: str | None = Query(default=None),
    db: Session = Depends(get_db),
    context: CurrentRequestContext = Depends(get_current_request_context),
    market_service: MarketService = Depends(get_market_service),
) -> dict:
    """
    Return a high-level market overview for a city.
    """
    return market_service.get_overview(db, city, country, context.tenant_id)


@router.get(
    "/{city}/demographics",
    summary="Get market demographics",
)
def get_market_demographics(
    city: str,
    country: str | None = Query(default=None),
    db: Session = Depends(get_db),
    market_service: MarketService = Depends(get_market_service),
) -> dict:
    """
    Return market demographics for a city.
    """
    demographics = market_service.get_demographics_by_region(db, city, country)
    return {"city": city, "country": country, "demographics": demographics}


@router.get(
    "/{city}/business-density",
    summary="Get business density",
)
def get_business_density(
    city: str,
    country: str | None = Query(default=None),
    business_type: str | None = Query(default=None),
    db: Session = Depends(get_db),
    market_service: MarketService = Depends(get_market_service),
) -> dict:
    """
    Return business density information for a city, optionally filtered by business
    type.
    """
    density = market_service.get_business_density(db, city, country, business_type)
    return {
        "city": city,
        "country": country,
        "business_type": business_type,
        "business_density": density,
    }
