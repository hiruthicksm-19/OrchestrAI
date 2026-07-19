"""
API Dependencies

Centralized dependency injection for FastAPI routes.

This module contains all dependencies that are injected into route handlers
using FastAPI's Depends() mechanism.

Current dependencies: None (Phase 2 Milestone 1)

Future dependencies to add:
- get_db_session() - Database session (Phase 2 Milestone 2)
- get_current_user() - Current authenticated user (Phase 3)
- get_settings() - Application settings (Phase 3)
- get_debate_engine() - DebateEngine instance (Phase 2 Milestone 2)

Example usage in routes:
    from fastapi import Depends
    from app.api.dependencies import get_debate_engine

    @router.post("/debates")
    async def create_debate(question: str, engine = Depends(get_debate_engine)):
        result = await engine.run(question)
        return result

Note:
    Keep dependencies lightweight and focus on providing instances
    or validating preconditions. Complex logic belongs in services.
"""

# Placeholder for future dependencies
pass
