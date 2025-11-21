from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from api.dependencies import CurrentRequestContext, get_current_request_context, get_db
from services.market_service import MarketService

router = APIRouter()


def get_market_service() -> MarketService:
    return MarketService()


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
    status_code=status.HTTP_501_NOT_IMPLEMENTED,
)
def get_market_demographics(
    city: str, market_service: MarketService = Depends(get_market_service)
) -> dict:
    """
    Return market demographics for a city.
    """
    return {"detail": "Not implemented"}
