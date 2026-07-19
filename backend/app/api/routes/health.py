"""
Health Check Endpoint

GET /health - Health check endpoint

This endpoint allows clients and load balancers to verify
the API is running and healthy.

Future health checks (not yet implemented):
- Database connectivity
- Provider API connectivity
- Service availability
"""

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class HealthStatus(BaseModel):
    """Response model for health check."""

    status: str


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
