"""
Async SQLAlchemy Database Session Management

This module manages the database connection lifecycle using modern SQLAlchemy 2.x patterns.

Key components:
- Async Engine: Manages connection pooling
- Async Session Factory: Creates sessions per request
- Database Dependency: FastAPI dependency for session injection
- Connection Testing: Verifies database connectivity

Design Principles:
- Every request gets its own AsyncSession
- Sessions are automatically closed after use
- Connection pooling is configured for production
- All operations are async-first
- No global session state

Usage:
    from app.database.session import get_db
    from fastapi import Depends
    
    @app.get("/data")
    async def get_data(session = Depends(get_db)):
        # session is an AsyncSession instance
        result = await session.execute(...)
        return result
"""

from typing import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
)

from app.core.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class DatabaseManager:
    """Manages database connection and session lifecycle."""

    def __init__(self):
        self._engine: AsyncEngine | None = None
        self._session_factory: async_sessionmaker | None = None
        self._is_connected: bool = False

    def initialize(self) -> None:
        """Initialize database engine and session factory."""
        if self._engine is not None:
            return

        # Validate DATABASE_URL is configured
        if not settings.database.url:
            logger.warning(
                "DATABASE_URL not configured. "
                "Database operations will not be available. "
                "Set DATABASE_URL in .env to enable PostgreSQL integration."
            )
            return

        try:
            # Create async engine with production-friendly configuration
            self._engine = create_async_engine(
                url=settings.database.url,
                echo=settings.app.debug,  # Log SQL in debug mode
                echo_pool=settings.app.debug,  # Log connection pool in debug mode
                future=True,  # Use SQLAlchemy 2.0 behavior
                # Connection pool configuration
                pool_size=10,  # Number of connections to maintain
                max_overflow=5,  # Maximum overflow connections
                pool_recycle=3600,  # Recycle connections after 1 hour
                pool_pre_ping=True,  # Ping connections before using
                # Timeout configuration
                connect_args={
                    "timeout": 30,  # Connection timeout
                    "command_timeout": 30,  # Command timeout
                },
            )

            # Create session factory
            self._session_factory = async_sessionmaker(
                bind=self._engine,
                class_=AsyncSession,
                expire_on_commit=False,  # Don't expire objects after commit
                autoflush=False,  # Explicit flushing
                autocommit=False,  # Explicit commits
            )

            logger.info(
                "✓ Database engine initialized | "
                f"URL={self._mask_url(settings.database.url)}"
            )

        except Exception as e:
            logger.error(f"✗ Failed to initialize database engine: {e}")
            raise

    async def connect(self) -> None:
        """Test database connection."""
        if not self._engine:
            logger.warning("Database engine not initialized")
            return

        try:
            async with self._engine.begin() as conn:
                await conn.execute(text("SELECT 1"))
            self._is_connected = True
            logger.info("✓ Database connection successful")
        except Exception as e:
            self._is_connected = False
            logger.error(f"✗ Database connection failed: {e}")
            raise

    async def disconnect(self) -> None:
        """Close database connections."""
        if self._engine:
            await self._engine.dispose()
            self._is_connected = False
            logger.info("✓ Database disconnected")

    async def health_check(self) -> dict:
        """Check database health."""
        if not self._engine:
            return {"status": "unhealthy", "reason": "engine_not_initialized"}

        try:
            async with self._engine.begin() as conn:
                await conn.execute(text("SELECT 1"))
            return {"status": "healthy", "database": "connected"}
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {"status": "unhealthy", "database": "disconnected"}

    def get_session_factory(self) -> async_sessionmaker:
        """Get the session factory."""
        if not self._session_factory:
            raise RuntimeError(
                "Database not initialized. Call initialize() first."
            )
        return self._session_factory

    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Create a new database session."""
        if not self._session_factory:
            raise RuntimeError(
                "Database not initialized. Call initialize() first."
            )

        async with self._session_factory() as session:
            try:
                logger.debug("Database session created")
                yield session
                await session.commit()
                logger.debug("Database session committed")
            except Exception as e:
                await session.rollback()
                logger.error(f"Database session error: {e}")
                raise
            finally:
                await session.close()
                logger.debug("Database session closed")

    @property
    def engine(self) -> AsyncEngine | None:
        """Get the database engine."""
        return self._engine

    @property
    def is_connected(self) -> bool:
        """Check if database is connected."""
        return self._is_connected

    @staticmethod
    def _mask_url(url: str) -> str:
        """Mask sensitive information in database URL for logging."""
        # Replace password with masked value
        if "@" in url:
            scheme_user = url.split("@")[0]
            host_db = url.split("@")[1]
            return f"{scheme_user.rsplit(':', 1)[0]}:***@{host_db}"
        return url


# Singleton instance
_db_manager = DatabaseManager()


# FastAPI dependency for session injection
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency to inject database session into routes.

    Usage:
        @app.get("/data")
        async def get_data(session = Depends(get_db)):
            result = await session.execute(...)
            return result
    """
    async for session in _db_manager.get_session():
        yield session


# Module-level functions for initialization and cleanup
async def initialize_db() -> None:
    """Initialize database connection pool."""
    _db_manager.initialize()
    try:
        await _db_manager.connect()
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        # Don't raise - allow app to start even if DB is unavailable
        # Health checks will report the status


async def close_db() -> None:
    """Close database connections."""
    await _db_manager.disconnect()


async def get_db_health() -> dict:
    """Get database health status."""
    return await _db_manager.health_check()


async def get_session_factory() -> async_sessionmaker:
    """Get the session factory for manual session creation."""
    return _db_manager.get_session_factory()
