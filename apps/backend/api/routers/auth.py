from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from api.config import get_settings
from api.dependencies import CurrentRequestContext, get_current_request_context, get_db
from api.schemas.auth import DevLoginRequest, TokenResponse
from api.security.jwt import create_access_token
from repositories.tenant_repository import TenantRepository
from repositories.user_repository import UserRepository
from services.auth_service import AuthService

router = APIRouter()


def get_auth_service() -> AuthService:
    return AuthService(
        user_repository=UserRepository(),
        tenant_repository=TenantRepository(),
    )


@router.post(
    "/login",
    summary="Login",
)
def login(
    request: DevLoginRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    """
    Temporary dev login that issues an access token.

    TODO: Replace with real email/password authentication when password fields
    and refresh tokens are implemented.
    """
    _ = auth_service
    settings = get_settings()
    token = create_access_token(
        user_id=request.user_id,
        tenant_id=request.tenant_id,
        role=request.role,
        settings=settings,
    )
    return TokenResponse(access_token=token)


@router.get(
    "/me",
    summary="Get current user context",
)
def get_current_user(
    db: Session = Depends(get_db),
    context: CurrentRequestContext = Depends(get_current_request_context),
    auth_service: AuthService = Depends(get_auth_service),
) -> dict:
    """
    Returns the current user's profile and tenant context.
    """
    return auth_service.get_current_user_profile(db, context.user_id)
