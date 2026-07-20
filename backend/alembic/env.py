"""
Alembic Migration Environment Configuration

This file handles all database migrations using SQLAlchemy async patterns.

The run_migrations_online() function is called by the alembic command.
The configuration is loaded from app.core.config for consistency.

For async migrations, we use asyncio to run synchronous migration operations.

Migration examples:

    # Auto-generate migration from model changes
    alembic revision --autogenerate -m "Add user table"
    
    # Apply migrations
    alembic upgrade head
    
    # Revert to previous migration
    alembic downgrade -1
"""

import asyncio
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine
from alembic import context

# Import configuration and models
from app.core.config import settings
from app.database.base import Base

# Import all models so Alembic can detect them
from app.database.models import (
    User,
    Debate,
    Message,
    Feedback,
    APIUsage,
)

# this is the Alembic Config object
config = context.config

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Use our database URL from settings
if settings.database.url:
    config.set_main_option("sqlalchemy.url", settings.database.url)

# Set target metadata for 'autogenerate' support
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection) -> None:
    """Run migrations with the given connection."""
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """
    Run migrations in 'online' mode.

    In this scenario we need to create an Engine and associate a connection
    with the context.
    """
    url = config.get_main_option("sqlalchemy.url")
    
    if not url:
        raise ValueError(
            "sqlalchemy.url not configured. "
            "Set DATABASE_URL in .env file."
        )

    # Create async engine
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = url
    
    engine = create_async_engine(
        url,
        poolclass=pool.NullPool,
        echo=False,
    )

    async with engine.begin() as connection:
        await connection.run_sync(do_run_migrations)

    await engine.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
