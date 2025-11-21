from fastapi import APIRouter, Depends, status

from services.auth_service import AuthService

router = APIRouter()


def get_auth_service() -> AuthService:
    return AuthService()


@router.post(
    "/login",
    summary="Login",
    status_code=status.HTTP_501_NOT_IMPLEMENTED,
)
def login(auth_service: AuthService = Depends(get_auth_service)) -> dict:
    """
    Authenticate a user and return a JWT + tenant context.
    """
    return {"detail": "Not implemented"}


@router.get(
    "/me",
    summary="Get current user context",
    status_code=status.HTTP_501_NOT_IMPLEMENTED,
)
def get_current_user(auth_service: AuthService = Depends(get_auth_service)) -> dict:
    """
    Returns the current user's profile and tenant context.
    """
    return {"detail": "Not implemented"}
