"""
Root Endpoint - Application Metadata

GET / - Returns application metadata (version, status, etc.)

This endpoint allows clients to verify the API is running
and retrieve basic application information.
"""

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class ApplicationInfo(BaseModel):
    """Response model for application information."""

    application: str
    version: str
    status: str


@router.get("/", response_model=ApplicationInfo)
async def root() -> ApplicationInfo:
    """
    Get application metadata.

    Returns:
        ApplicationInfo: Application name, version, and status.

    Example:
        GET /
        200 OK
        {
            "application": "DebateAI",
            "version": "1.0.0",
            "status": "running"
        }
    """
    return ApplicationInfo(
        application="DebateAI",
        version="1.0.0",
        status="running",
    )
