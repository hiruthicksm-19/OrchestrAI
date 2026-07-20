"""
API Routes Module

Exports all routers for registration in the main FastAPI application.

This module centralizes router imports so main.py can simply import
the routers without knowing about individual route files.

Router organization:
- root: Application metadata endpoint
- health: Health check endpoints
- debates: Debate CRUD and execution endpoints

Future routers to be added:
- feedback: Feedback/rating endpoints
- analytics: Provider analytics endpoints
- admin: Admin endpoints
- auth: Authentication endpoints (Phase 3)
"""

from app.api.routes.root import router as root_router
from app.api.routes.health import router as health_router
from app.api.routes.debates import router as debates_router

__all__ = [
    "root_router",
    "health_router",
    "debates_router",
]
