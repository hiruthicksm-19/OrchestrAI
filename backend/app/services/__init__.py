"""
Services Layer

Business logic layer between routes and repositories.

Services handle:
- Business rule validation
- Orchestration
- Coordination between repositories
- Error handling
- Formatting responses

Services do NOT:
- Handle HTTP concerns
- Create sessions
- Know about FastAPI

Usage:
    service = DebateService(session)
    debate = await service.create_debate(question)
"""

from app.services.debate_service import DebateService

__all__ = ["DebateService"]
