"""
Shared FastAPI dependency functions.

Use this module to define common dependency-injected objects,
such as database sessions, current user, settings, etc.
"""

from collections.abc import AsyncGenerator

# from .config import get_settings


async def get_db() -> AsyncGenerator[None, None]:
    """
    Placeholder for a database session dependency.

    Replace the body of this function with actual DB session creation
    and teardown when you introduce persistence.
    """
    # db = SessionLocal()
    # try:
    #     yield db
    # finally:
    #     db.close()
    yield


