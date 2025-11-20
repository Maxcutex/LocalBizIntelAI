"""
Shared FastAPI dependency functions.

Use this module to define common dependency-injected objects,
such as database sessions, current user, settings, etc.
"""

from collections.abc import Generator

from apps.backend.models.db import SessionLocal


def get_db() -> Generator:
    """
    Database session dependency.

    Yields a SQLAlchemy session that is closed after the request ends.
    Use in route signatures as:

        def endpoint(db: Session = Depends(get_db)):
            ...
    """

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


