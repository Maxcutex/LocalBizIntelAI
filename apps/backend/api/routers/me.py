"""User-context routes for the authenticated caller."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from api.dependencies import CurrentRequestContext, get_current_request_context, get_db
from repositories.tenant_repository import TenantRepository
from repositories.user_repository import UserRepository
from services.auth_service import AuthService
from services.dependencies import AuthServiceDependencies

router = APIRouter()


def get_auth_service() -> AuthService:
    """Construct an `AuthService` with concrete repositories for request DI."""
    return AuthService(
        AuthServiceDependencies(
            user_repository=UserRepository(),
            tenant_repository=TenantRepository(),
        )
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
    Return the current user's profile and current tenant summary.

    Example:
        `GET /me`
    """
    return auth_service.get_current_user_profile(db, context.user_id)
