from fastapi import APIRouter, Depends, status

from services.market_service import MarketService

router = APIRouter()


def get_market_service() -> MarketService:
    return MarketService()


@router.get(
    "/{city}/overview",
    summary="Get market overview",
    status_code=status.HTTP_501_NOT_IMPLEMENTED,
)
def get_market_overview(
    city: str, market_service: MarketService = Depends(get_market_service)
) -> dict:
    """
    Return a high-level market overview for a city.
    """
    return {"detail": "Not implemented"}


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
