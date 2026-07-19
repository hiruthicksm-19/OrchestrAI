# Backend Architecture — DebateAI Phase 1 → Phase 2

## Directory Structure

```
backend/
  app/
    core/              Settings, Agent Registry, Logging, Exceptions, Constants
    api/               FastAPI routes (Phase 2)
    services/          Business logic orchestration (Phase 2)
    database/          SQLAlchemy models, repositories (Phase 2)
    schemas/           Pydantic validation schemas (Phase 2)
    debate/            Debate orchestration, engine, strategy
    agents/            Agent classes, agent factory
    providers/         Provider abstraction, implementations
    prompts/           Prompt Manager, prompt templates
    utils/             Logging, exceptions, utilities
  tests/               Unit and integration tests
  alembic/             Database migrations (Phase 2)
  main.py              Terminal CLI entrypoint
```

## Layer Responsibilities

### core/
**Contains:** Settings, Agent Registry, Logging, Exceptions, Constants, Security

- `settings.py` — Pydantic Settings, loads .env, validates configuration
- `agent_registry.py` — Agent configuration registry, role → agent mapping
- `logging.py` — Centralized logging configuration (future)
- `exceptions.py` — Application exception hierarchy
- `constants.py` — Application constants (future)
- `security.py` — Security utilities (future)

**No business logic. No provider code. No database code.**

### api/
**Contains:** FastAPI routes, request/response handlers

**Phase 2 only.** Will contain:
- `/debates` — Create, list, status, results
- `/health` — Health check endpoint
- Error handling middleware
- CORS configuration

**No business logic in routes. Routes must delegate to services.**

### services/
**Contains:** Application services that orchestrate multiple layers

**Phase 2 only.** Examples:
- `DebateService` — Uses DebateEngine, repositories, providers
- `ProviderService` — Provider lifecycle, failover
- `AuthService` — User authentication (future)
- `RAGService` — Retrieval-augmented generation (future)

**Services contain business logic that spans multiple modules.**

### database/
**Contains:** SQLAlchemy models, repositories, session management

**Phase 2 only.** Will contain:
- `base.py` — SQLAlchemy declarative base
- `session.py` — Session factory, transaction management
- `models/` — SQLAlchemy ORM models (Debate, Message, etc.)
- `repositories/` — Data access layer (Repository pattern)

**No business logic. No provider code. No agent logic.**

### schemas/
**Contains:** Pydantic models for API validation

**Phase 2 only.** Examples:
- `DebateRequest` — POST /debates request body
- `DebateResponse` — Debate response model
- `MessageResponse` — Single message model
- `HealthResponse` — Health check response

**These are request/response contracts, not ORM models.**

### debate/
**Contains:** Debate orchestration and engine

- `debate_engine.py` — Main orchestrator, runs debate stages
- `debate_state.py` — DebateState, DebateMessage, DebateResult
- `debate_strategy.py` — Strategy definitions, selection logic
- `question_classifier.py` — Question type classification (heuristic)

**Pure orchestration. No FastAPI. No database. No provider logic.**

### agents/
**Contains:** Agent implementations and factory

- `base_agent.py` — Abstract agent interface
- `research_agent.py` — Research/proponent agent
- `opponent_agent.py` — Adversarial opponent agent
- `consensus_agent.py` — Consensus synthesizer
- `agent_factory.py` — Agent instantiation by role

**No provider-specific code. No database. No routes.**

### providers/
**Contains:** Provider abstraction and implementations

- `base_provider.py` — Abstract provider interface
- `groq_provider.py` — Groq API wrapper
- `mistral_provider.py` — Mistral API wrapper
- `cerebras_provider.py` — Cerebras API wrapper
- `openai_provider.py` — OpenAI API wrapper
- `provider_factory.py` — Provider instantiation by name

**Only provider abstraction and vendor-specific logic.**

### prompts/
**Contains:** Prompt management and templates

- `prompt_manager.py` — Loads/renders YAML prompt templates
- `*.yaml` — System and strategy prompts

**No agent logic. No provider logic. No database.**

### utils/
**Contains:** Reusable utilities

- `logger.py` — Centralized loguru configuration
- `exceptions.py` — Exception hierarchy

**No business logic. No domain-specific code.**

## Import Dependencies

Valid imports (leaf → root):
- `agents` → `core`, `prompts`, `utils`, `providers`
- `debate` → `agents`, `core`, `utils`
- `providers` → `core`, `utils`
- `prompts` → `core`, `utils`

Forbidden imports:
- `core` → anything
- `utils` → anything
- Circular imports (e.g., `agents` → `debate` ← `agents`)

## Phase 2 Integration Points

### Adding FastAPI routes (`api/`)
```python
# api/routes/debates.py
from app.services.debate_service import DebateService

@router.post("/debates")
async def create_debate(request: DebateRequest, service: DebateService = Depends()):
    result = await service.run_debate(request.question)
    return DebateResponse.from_result(result)
```

### Adding database models (`database/`)
```python
# database/models.py
from sqlalchemy import Column, String, Text, DateTime
from app.database.base import Base

class DebateModel(Base):
    __tablename__ = "debates"
    id = Column(String, primary_key=True)
    question = Column(Text)
    ...
```

### Adding repository pattern (`database/repositories/`)
```python
# database/repositories/debate_repository.py
class DebateRepository:
    def save(self, debate: DebateState) -> str:
        model = DebateModel.from_state(debate)
        session.add(model)
        session.commit()
        return model.id
```

### Adding services (`services/`)
```python
# services/debate_service.py
class DebateService:
    def __init__(self, engine: DebateEngine, repo: DebateRepository):
        self.engine = engine
        self.repo = repo
    
    async def run_debate(self, question: str) -> str:
        result = await self.engine.run(question)
        debate_id = self.repo.save(result.state)
        return debate_id
```

## Backward Compatibility

All Phase 1 code continues to work unchanged:
- `DebateEngine` still imports from `app.debate.*`
- Agents still import from `app.agents.*`
- Providers still import from `app.providers.*`
- `main.py` still runs the CLI

Phase 2 will add new modules without touching existing business logic.

## Testing Strategy

- Unit tests: Test individual modules in isolation
- Integration tests: Test DebateEngine with mock providers
- E2E tests: Test full terminal workflow

Tests live in `tests/` and follow the app structure:
- `tests/test_debate_engine.py`
- `tests/test_agents.py`
- `tests/test_providers.py`
