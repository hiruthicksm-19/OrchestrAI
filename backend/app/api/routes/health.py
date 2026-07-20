"""
Health Check Endpoint

GET /health - Basic health check endpoint
GET /health/database - Database connectivity check

This endpoint allows clients and load balancers to verify
the API is running and optionally check database status.

Future health checks (not yet implemented):
- Provider API connectivity
- Service availability
"""

from fastapi import APIRouter
from pydantic import BaseModel

from app.database import get_db_health

router = APIRouter()


class HealthStatus(BaseModel):
    """Response model for health check."""

    status: str


class DatabaseHealthStatus(BaseModel):
    """Response model for database health check."""

    status: str
    database: str


@router.get("/health", response_model=HealthStatus)
async def health() -> HealthStatus:
    """
    Get health status of the API.

    Returns:
        HealthStatus: Current health status.

    Note:
        This basic health check only verifies the backend is running.
        Database and provider health checks will be added in future milestones.

    Example:
        GET /health
        200 OK
        {
            "status": "healthy"
        }
    """
    return HealthStatus(status="healthy")


@router.get("/health/database", response_model=DatabaseHealthStatus)
async def health_database() -> DatabaseHealthStatus:
    """
    Get database health status.

    Returns:
        DatabaseHealthStatus: Database connection status.

    Attempts to:
    1. Connect to PostgreSQL
    2. Execute a simple query (SELECT 1)
    3. Return connection status

    Returns:
        - status: "healthy" or "unhealthy"
        - database: "connected" or "disconnected"

    Example:
        GET /health/database
        200 OK
        {
            "status": "healthy",
            "database": "connected"
        }

    Error:
        GET /health/database
        503 Service Unavailable
        {
            "status": "unhealthy",
            "database": "disconnected"
        }
    """
    health_info = await get_db_health()
    
    # Return 503 if database is unhealthy
    status_code = 200 if health_info["status"] == "healthy" else 503
    
    return DatabaseHealthStatus(
        status=health_info["status"],
        database=health_info.get("database", "unknown"),
    )
