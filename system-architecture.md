# 02 - System Architecture Document (SAD)

# Project Name

**DebateAI – Production-Ready Multi-Agent AI Debate Platform**

Version: **1.0**

---

# 1. Purpose

This document defines the complete architecture of DebateAI, including its software components, data flow, communication between services, AI orchestration, database interactions, deployment architecture, and scalability considerations.

The objective is to ensure the system remains modular, maintainable, and easy to extend.

---

# 2. High-Level Architecture

```text
                    User
                      │
              HTTPS Request
                      │
                      ▼
              React Frontend
                      │
                REST API Calls
                      │
                      ▼
              FastAPI Backend
                      │
        ┌─────────────┴─────────────┐
        │                           │
        ▼                           ▼
 Authentication              Debate Engine
        │                           │
        │                    Debate Orchestrator
        │                           │
        │          ┌────────────────┴──────────────┐
        │          ▼                               ▼
        │    OpenAI Agent                   Gemini Agent
        │          │                               │
        │          └──────────────┬────────────────┘
        │                         ▼
        │                 Consensus Agent
        │                         │
        └───────────────┬─────────┘
                        ▼
                     MongoDB
```

---

# 3. System Components

## Frontend

Technology

* React
* Tailwind CSS
* Axios

Responsibilities

* Login
* Chat Interface
* Debate Timeline
* Chat History
* User Settings
* Display Streaming Responses

The frontend never communicates directly with the LLM APIs.

All requests go through FastAPI.

---

## Backend

Technology

* FastAPI
* Python

Responsibilities

* Authentication
* API Routing
* Debate Orchestration
* Validation
* Error Handling
* Logging
* MongoDB Operations

The backend is the heart of the application.

---

## AI Layer

The AI Layer consists of multiple agents.

Initially:

* OpenAI Agent
* Gemini Agent
* Consensus Agent

Each agent exposes the same interface.

Example:

```python
generate(prompt)
```

This allows additional providers to be added without changing the debate engine.

---

# 4. Debate Engine

The Debate Engine coordinates every debate.

Responsibilities

* Receive user question
* Call Agent A
* Call Agent B
* Store responses
* Generate critiques
* Execute debate rounds
* Invoke Consensus Agent
* Save complete debate

The Debate Engine never directly handles HTTP requests.

Only the API layer communicates with it.

---

# 5. Debate Workflow

```text
User Question
      │
      ▼
OpenAI Initial Response
      │
Gemini Initial Response
      │
OpenAI Critique
      │
Gemini Critique
      │
Consensus Agent
      │
Final Response
      │
Store Everything
```

---

# 6. Component Responsibilities

## API Layer

Responsible for

* Authentication endpoints
* Debate endpoints
* User endpoints
* Validation
* HTTP responses

---

## Debate Orchestrator

Responsible for

* Calling agents
* Managing debate rounds
* Building prompts
* Maintaining debate state
* Handling failures

---

## Agent Layer

Responsible for

* Sending prompts
* Receiving responses
* Formatting output
* Returning structured responses

Agents never communicate directly.

Only the orchestrator coordinates them.

---

## Database Layer

Responsible for

* Users
* Debates
* Messages
* Settings

No business logic should exist inside the database layer.

---

# 7. Request Flow

```text
User

↓

React

↓

POST /debate

↓

FastAPI

↓

Authentication

↓

Debate Engine

↓

OpenAI

↓

Gemini

↓

Consensus

↓

MongoDB

↓

JSON Response

↓

React
```

---

# 8. Authentication Flow

```text
User

↓

POST /login

↓

FastAPI

↓

MongoDB

↓

Verify Password

↓

Generate JWT

↓

Return Token

↓

Frontend Stores Token
```

Every protected request includes:

Authorization: Bearer JWT_TOKEN

---

# 9. Debate Sequence

Round 1

User asks question.

↓

OpenAI answers.

↓

Gemini answers.

---

Round 2

OpenAI critiques Gemini.

↓

Gemini critiques OpenAI.

---

Final

Consensus Agent reads:

* User Question
* OpenAI Responses
* Gemini Responses
* Debate History

↓

Generates final answer.

---

# 10. MongoDB Collections

## users

Stores

* Name
* Email
* Password Hash
* Profile Information

---

## debates

Stores

* Debate Title
* User ID
* Debate Configuration
* Created Date
* Updated Date

---

## messages

Stores

* Debate ID
* Round Number
* Agent Name
* Role
* Message
* Token Usage
* Latency
* Timestamp

---

# 11. Folder Responsibilities

```text
backend/

api/
    HTTP Endpoints

agents/
    OpenAI
    Gemini
    Consensus

debate/
    Debate Engine
    Debate Manager

database/
    MongoDB Connection

models/
    Database Models

schemas/
    Pydantic Schemas

services/
    Business Logic

config/
    Environment Variables

utils/
    Helper Functions

middleware/
    Authentication

tests/
    Unit Tests

main.py
```

---

# 12. Error Handling Strategy

Possible failures

* Invalid API Key
* OpenAI unavailable
* Gemini unavailable
* MongoDB unavailable
* Invalid JWT
* Timeout
* Rate Limit

Strategy

* Log error
* Retry when appropriate
* Return meaningful error
* Never expose secrets

---

# 13. Logging Strategy

Log

* User Login
* Debate Started
* Debate Completed
* API Latency
* Token Usage
* Errors

Never log

* Passwords
* API Keys
* JWT Tokens

---

# 14. Security

Security measures

* JWT Authentication
* Password Hashing (bcrypt)
* Environment Variables
* CORS Configuration
* Request Validation
* File Size Limits (future)
* HTTPS in Production

---

# 15. Deployment Architecture

```text
Browser

↓

Vercel

↓

FastAPI Backend

↓

MongoDB Atlas

↓

OpenAI API

↓

Gemini API
```

Docker will containerize

* Backend
* Frontend (optional for local development)
* Supporting services

---

# 16. Scalability

Future enhancements

* Redis Cache
* Background Workers
* Queue System
* Load Balancer
* PostgreSQL Analytics Database (optional)
* Vector Database (ChromaDB/Qdrant) for RAG

Current architecture should allow these additions with minimal refactoring.

---

# 17. Design Principles

* Single Responsibility Principle
* Separation of Concerns
* Provider-agnostic AI layer
* Stateless backend (except persistent storage)
* Configuration through environment variables
* Modular architecture
* Extensible agent framework

---

# 18. Future Agent Architecture

Current

```text
OpenAI

Gemini

Consensus
```

Future

```text
OpenAI

Gemini

Claude

DeepSeek

Llama

Research Agent

Fact Checker

Consensus Agent
```

Adding a new agent should require only implementing the common agent interface.

---

# 19. Performance Goals

* Login: < 500 ms (excluding network latency)
* Debate initialization: < 1 second
* Individual model response: dependent on provider
* Backend API overhead: minimal
* Support concurrent users without blocking by using asynchronous request handling

---

# 20. Architecture Summary

The architecture follows a layered design:

1. **Presentation Layer** – React UI
2. **API Layer** – FastAPI endpoints
3. **Business Layer** – Debate Engine & Services
4. **AI Layer** – OpenAI, Gemini, Consensus Agents
5. **Data Layer** – MongoDB
6. **Infrastructure Layer** – Docker, Vercel, MongoDB Atlas

Each layer has a clearly defined responsibility and communicates only with adjacent layers, making the application easier to test, maintain, and extend as new AI providers and features are added.
