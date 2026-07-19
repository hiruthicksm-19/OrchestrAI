"""
API Module

Contains all HTTP route handlers and API-related utilities.

Structure:
- routes/ - Individual route modules (root, health, debates, etc.)
- dependencies.py - Dependency injection for routes
- main.py - FastAPI application initialization (in app/)

This layer is responsible for:
- HTTP request/response handling
- Route organization
- Dependency injection
- OpenAPI documentation

The routes should NOT contain business logic.
Business logic belongs in services/ or the debate/ module.
"""
