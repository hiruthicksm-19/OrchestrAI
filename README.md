# DebateAI — Multi-Agent Adversarial Debate System

A production-grade multi-agent AI platform where three AI agents — each backed by a different provider — debate a question and synthesise the best possible answer.

**Current Phase:** Phase 1 (Terminal CLI) → Phase 2 (FastAPI + PostgreSQL)

## How it works

```
User Question
     │
     ▼
Classify question  (factual / debate / explanation / coding ...)
     │
     ▼
Select strategy    (Direct Answer / Full Adversarial Debate / ...)
     │
     ├── Simple ──► Research Agent ──► Consensus
     │
     └── Debate ──► Research Agent ║ Opponent Agent  (parallel)
                         │                │
                         └── Rebuttals ───┘           (parallel)
                                  │
                             Consensus Agent
                                  │
                            Final Answer
```

## Agents

| Agent | Provider | Model | Role |
|---|---|---|---|
| Research Agent | Groq | `llama-3.3-70b-versatile` | Defends one position |
| Opponent Agent | OpenAI | `gpt-4o-mini` | Argues the opposing position |
| Consensus Agent | Mistral | `mistral-large-latest` | Synthesises the best answer |

## Quick Start

**1. Clone the repository**
```bash
git clone https://github.com/hiruthicksm-19/OrchestrAI.git
cd OrchestrAI
```

**2. Create a virtual environment**
```bash
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # macOS / Linux
```

**3. Install dependencies**
```bash
pip install -r requirements.txt
```

**4. Configure API keys**
```bash
cp .env.example .env
# Edit .env and add your API keys
```

**5. Run the CLI**
```bash
cd backend
python main.py
```

## Project Structure

See [`backend/ARCHITECTURE.md`](backend/ARCHITECTURE.md) for detailed layer responsibilities.

```
backend/app/
  core/       Settings, Agent Registry, Logging, Exceptions
  api/        FastAPI routes (Phase 2)
  services/   Business logic services (Phase 2)
  database/   SQLAlchemy models (Phase 2)
  schemas/    Pydantic validation (Phase 2)
  debate/     Debate engine and orchestration
  agents/     Agent implementations
  providers/  Provider abstraction
  prompts/    Prompt manager and templates
  utils/      Logging, exceptions, utilities
```

## Design Principles

- **Provider-independent** — swap any model or provider in the registry
- **Prompt-driven** — all prompts live in `.yaml` files, never in code
- **Adaptive strategy** — question type determines workflow automatically
- **Parallel execution** — opening statements and rebuttals run concurrently
- **Clean architecture** — each layer has one responsibility
- **Production-ready** — structured for Phase 2 (FastAPI, PostgreSQL, tests)

## Supported Providers

**Current:**
- Groq
- Mistral
- Cerebras
- OpenAI

**Future (no code changes needed):**
- Claude (Anthropic)
- Gemini (Google)
- DeepSeek
- Ollama (local models)

## Phase 2 Roadmap

- [ ] FastAPI REST server
- [ ] PostgreSQL database
- [ ] SQLAlchemy ORM models
- [ ] Repository pattern
- [ ] Database migrations (Alembic)
- [ ] Authentication & authorization
- [ ] Unit and integration tests
- [ ] Docker containerization
- [ ] React frontend

## Development

For developers: see [`backend/ARCHITECTURE.md`](backend/ARCHITECTURE.md) for:
- Layer responsibilities and import rules
- How to add FastAPI routes
- How to add database models and repositories
- How to add services that orchestrate multiple layers

## License

MIT
