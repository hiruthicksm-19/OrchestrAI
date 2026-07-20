"""
Application Constants

This module contains all application-level constants.
These are immutable values that define the application's behavior.

Rules:
- Only true constants belong here (immutable, universal values)
- Configuration values belong in config.py
- Secrets should NEVER be here
- Environment-specific values belong in config.py
"""

# Supported AI Providers
SUPPORTED_PROVIDERS = [
    "groq",
    "mistral",
    "cerebras",
    "openai",
]

PROVIDER_DISPLAY_NAMES = {
    "groq": "Groq",
    "mistral": "Mistral",
    "cerebras": "Cerebras",
    "openai": "OpenAI",
}

# Supported Agent Roles
AGENT_ROLES = {
    "research": "Research Agent",
    "opponent": "Opponent Agent",
    "consensus": "Consensus Agent",
}

# Question Classification Types
QUESTION_TYPES = [
    "factual",
    "explanation",
    "comparison",
    "coding",
    "architecture",
    "debate",
    "reasoning",
    "creative",
]

# Debate Strategies
DEBATE_STRATEGIES = [
    "simple",  # Single stage: Research → Consensus
    "adversarial",  # Full debate: Research ║ Opponent → Rebuttals → Consensus
]

# Response Types in Debate
RESPONSE_TYPES = [
    "opening",
    "rebuttal",
    "consensus",
]

# HTTP Status Messages
HTTP_STATUS_MESSAGES = {
    200: "OK",
    201: "Created",
    204: "No Content",
    400: "Bad Request",
    401: "Unauthorized",
    403: "Forbidden",
    404: "Not Found",
    409: "Conflict",
    422: "Unprocessable Entity",
    500: "Internal Server Error",
    503: "Service Unavailable",
}

# Default Timeouts (in seconds)
DEFAULT_TIMEOUTS = {
    "provider_request": 60,
    "debate_engine": 300,
    "api_request": 30,
    "database_query": 10,
}

# Default Token Limits
DEFAULT_TOKEN_LIMITS = {
    "research_agent": 2048,
    "opponent_agent": 2048,
    "consensus_agent": 3000,
}

# Default Temperatures
DEFAULT_TEMPERATURES = {
    "research_agent": 0.7,
    "opponent_agent": 0.6,
    "consensus_agent": 0.5,
}

# Retry Configuration
RETRY_CONFIG = {
    "max_attempts": 3,
    "backoff_factor": 2.0,
    "max_backoff": 60,
}

# API Documentation
API_TITLE = "DebateAI API"
API_DESCRIPTION = "Production-ready Multi-Agent AI Debate Platform"
API_VERSION = "2.0.0"
API_DOCS_URL = "/docs"
API_REDOC_URL = "/redoc"
API_OPENAPI_URL = "/openapi.json"

# CORS Settings
CORS_ALLOW_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:8080",
    "http://127.0.0.1:3000",
]

# Logging Configuration
LOG_FORMATS = {
    "json": "%(message)s",
    "text": "%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d - %(message)s",
}

# Database Configuration
DATABASE_POOL_SIZE = 10
DATABASE_MAX_OVERFLOW = 5
DATABASE_POOL_TIMEOUT = 30
DATABASE_ECHO = False  # Set to True for SQL debugging

# Cache Configuration
CACHE_TTL = {
    "agent_config": 3600,  # 1 hour
    "prompts": 7200,  # 2 hours
    "provider_status": 300,  # 5 minutes
}
