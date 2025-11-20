"""
Database setup module.

Defines the SQLAlchemy engine, session factory, and declarative base
for ORM models. All ORM models should inherit from `Base`.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from api.config import get_settings


class Base(DeclarativeBase):
    """Base class for all ORM models."""


settings = get_settings()

engine = create_engine(
    settings.sqlalchemy_database_uri,
    echo=settings.debug,
    future=True,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    future=True,
)


def get_engine():
    """Expose engine for migration tools and advanced use-cases."""

    return engine


