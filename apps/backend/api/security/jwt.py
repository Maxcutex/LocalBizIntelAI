"""JWT helpers for bearer authentication."""

from datetime import datetime, timedelta, timezone
from uuid import UUID

from jose import JWTError, jwt  # type: ignore[import-untyped]

from api.config import Settings


def create_access_token(
    *, user_id: UUID, tenant_id: UUID, role: str, settings: Settings
) -> str:
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(minutes=settings.jwt_access_token_ttl_min)
    payload = {
        "sub": str(user_id),
        "tenant_id": str(tenant_id),
        "role": role,
        "iss": settings.jwt_issuer,
        "aud": settings.jwt_audience,
        "iat": int(now.timestamp()),
        "exp": int(expires_at.timestamp()),
    }
    return jwt.encode(
        payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm
    )


def decode_access_token(*, token: str, settings: Settings) -> dict:
    return jwt.decode(
        token,
        settings.jwt_secret_key,
        algorithms=[settings.jwt_algorithm],
        issuer=settings.jwt_issuer,
        audience=settings.jwt_audience,
    )


def try_verify_access_token(*, token: str, settings: Settings) -> dict | None:
    try:
        return decode_access_token(token=token, settings=settings)
    except JWTError:
        return None
