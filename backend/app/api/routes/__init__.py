"""
API Routes Module

Exports all routers for registration in the main FastAPI application.

This module centralizes router imports so main.py can simply import
the routers without knowing about individual route files.

Future routers to be added:
- debate_router - POST /debates, GET /debates/{id}, etc.
- admin_router - Admin endpoints
- auth_router - Authentication endpoints (Phase 3)
"""

from app.api.routes.root import router as root_router
from app.api.routes.health import router as health_router

__all__ = [
    "root_router",
    "health_router",
]
