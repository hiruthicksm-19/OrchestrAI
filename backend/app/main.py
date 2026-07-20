"""
DebateAI FastAPI Application

Production-ready REST API for the Multi-Agent Adversarial Debate Platform.

This is the main entry point for the FastAPI application. It:
- Initializes the FastAPI app with metadata
- Registers all routers
- Configures middleware
- Initializes database connections
- Provides the main entry point for production servers

Configuration is loaded from app/core/config.py
Database configuration loaded from app/core/config.py
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import root_router, health_router, debates_router
from app.core.config import settings
from app.core.constants import API_TITLE, API_DESCRIPTION, API_VERSION
from app.database import initialize_db, close_db
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Create FastAPI application with metadata from configuration
app = FastAPI(
    title=API_TITLE,
    description=API_DESCRIPTION,
    version=API_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# CORS middleware (allow requests from localhost during development)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change to specific origins in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(root_router, tags=["root"])
app.include_router(health_router, tags=["health"])
app.include_router(debates_router, tags=["debates"])


# Application lifecycle hooks
@app.on_event("startup")
async def startup_event() -> None:
    """Called when application starts."""
    logger.info(f"✓ DebateAI {settings.app.version} starting in {settings.app.environment} mode")
    logger.info(f"✓ Server: {settings.server.host}:{settings.server.port}")
    logger.info(f"✓ Default AI Provider: {settings.ai.provider}")
    logger.info(f"✓ Parallel Execution: {settings.debate.enable_parallel_execution}")
    # Initialize database
    logger.info("✓ Initializing database connection pool...")
    await initialize_db()


@app.on_event("shutdown")
async def shutdown_event() -> None:
    """Called when application shuts down."""
    logger.info("✓ Closing database connections...")
    await close_db()
    logger.info("✓ DebateAI shutting down")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host=settings.server.host,
        port=settings.server.port,
        reload=settings.app.debug,
    )
