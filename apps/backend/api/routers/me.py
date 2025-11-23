from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from api.dependencies import CurrentRequestContext, get_current_request_context, get_db
from repositories.tenant_repository import TenantRepository
from repositories.user_repository import UserRepository
from services.auth_service import AuthService

router = APIRouter()


def get_auth_service() -> AuthService:
    return AuthService(
        user_repository=UserRepository(),
        tenant_repository=TenantRepository(),
    )


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
