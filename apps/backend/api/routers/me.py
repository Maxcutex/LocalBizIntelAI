from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from api.dependencies import CurrentRequestContext, get_current_request_context, get_db
from services.auth_service import AuthService

router = APIRouter()


def get_auth_service() -> AuthService:
    return AuthService()


@router.get(
    "/me",
    summary="Get current user profile and tenant context",
)
def get_me(
    db: Session = Depends(get_db),
    context: CurrentRequestContext = Depends(get_current_request_context),
    auth_service: AuthService = Depends(get_auth_service),
) -> dict:
    """
    Returns the current user's profile and current tenant summary.
    """
    return auth_service.get_current_user_profile(db, context.user_id)
