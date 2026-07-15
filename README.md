# DebateAI — Multi-Agent Adversarial Debate System

A production-grade multi-agent AI platform where three AI agents — each backed by a different provider — debate a question and synthesise the best possible answer.

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

## Setup

**1. Clone the repository**
```bash
git clone <your-repo-url>
cd chatbot
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

**5. Run**
```bash
cd debateai
python -m backend.main
```

## Project structure

```
debateai/backend/
  agents/       Research, Opponent, Consensus agent classes
  config/       Settings, Agent Registry
  debate/       Question Classifier, Strategy Selector, Engine, State
  prompts/      YAML prompt templates + Prompt Manager
  providers/    Groq, Mistral, Cerebras, OpenAI wrappers
  utils/        Logger, Exceptions
  main.py       Terminal entrypoint
```

## Design principles

- **Provider-independent** — swap any model or provider in one line (the registry)
- **Prompt-driven** — all prompts live in `.yaml` files, never in Python code
- **Adaptive strategy** — question type determines the workflow automatically
- **Parallel execution** — opening statements and rebuttals run concurrently
- **Clean architecture** — each layer has one responsibility

## Supported providers

Groq · Mistral · Cerebras · OpenAI

Designed to support: Claude · Gemini · DeepSeek · Ollama (local models) without architectural changes.

## Version

**v1.0** — Terminal-only debate engine. FastAPI, MongoDB, React frontend, and Docker coming in future versions.
