"""Health check routes for uptime monitoring and load balancers."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/", summary="Health check")
async def health_check() -> dict:
    """
    Simple health-check endpoint for uptime monitoring.
    """
    return {"status": "ok"}
