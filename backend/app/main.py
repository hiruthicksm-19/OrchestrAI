"""
DebateAI FastAPI Application

Production-ready REST API for the Multi-Agent Adversarial Debate Platform.

This is the main entry point for the FastAPI application. It:
- Initializes the FastAPI app with metadata
- Registers all routers
- Configures middleware (if needed)
- Provides the main entry point for production servers

Phase 2 Milestone 1: Foundation setup (no database, auth, or logging yet)
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import root_router, health_router

# Create FastAPI application with metadata
app = FastAPI(
    title="DebateAI API",
    description="Production-ready Multi-Agent AI Debate Platform",
    version="1.0.0",
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


# Application lifecycle hooks (for future use)
@app.on_event("startup")
async def startup_event() -> None:
    """Called when application starts."""
    pass


@app.on_event("shutdown")
async def shutdown_event() -> None:
    """Called when application shuts down."""
    pass


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
