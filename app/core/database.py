"""Async SQLAlchemy engine, session factory, and FastAPI dependency."""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool

from app.core.config import get_settings


class Base(DeclarativeBase):
    """Shared declarative base for all SQLAlchemy models."""
    pass


def _create_engine():
    settings = get_settings()
    return create_async_engine(
        settings.database_url,
        # Connection pool tuned for ~3,000 concurrent users hitting a moderate
        # number of DB operations. Keeps connections warm; overflow allows bursts.
        pool_size=10,
        max_overflow=20,
        # poolclass=NullPool,
        pool_timeout=30,
        pool_recycle=1800,  # Recycle connections every 30 min to avoid stale state
        pool_pre_ping=True,  # Test connection health before use
        echo=not get_settings().is_production,  # SQL logging in dev only
        connect_args={
        "statement_cache_size": 0,
        # "prepared_statement_cache_size": 0,
        # "prepared_statement_name_func": lambda: "",
    },
    )


# engine = _create_engine()
settings = get_settings()

engine = create_async_engine(
    settings.database_url,
    poolclass=NullPool,
    connect_args={
        "statement_cache_size": 0,
    },
)


AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields an async database session per request."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
