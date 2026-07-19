# 07 - Deployment Guide

# Project

**DebateAI – Production-Ready Multi-Agent AI Debate Platform**

Version: **1.0**

---

# 1. Objective

This guide describes how to deploy DebateAI from a local development environment to a production-ready cloud environment.

The deployment should be:

* Secure
* Reliable
* Repeatable
* Easy to maintain
* Easy to update

---

# 2. Production Architecture

```text id="cvmr0i"
                 User
                   │
                   ▼
            React Frontend
                (Vercel)
                   │
            HTTPS Requests
                   │
                   ▼
          FastAPI Backend
         (Railway / Render)
                   │
         ┌─────────┼─────────┐
         ▼                   ▼
 MongoDB Atlas        AI Providers
                          │
             OpenAI / Gemini APIs
```

---

# 3. Infrastructure

## Frontend

* React
* Tailwind CSS

Hosting

* Vercel

---

## Backend

* FastAPI
* Python

Hosting

* Railway

or

* Render

---

## Database

MongoDB Atlas

---

## AI Providers

* OpenAI
* Gemini

---

# 4. Environment Variables

Backend

```text id="xgdbfc"
OPENAI_API_KEY

GEMINI_API_KEY

MONGODB_URI

JWT_SECRET_KEY

JWT_ALGORITHM

ACCESS_TOKEN_EXPIRE_MINUTES

APP_ENV

FRONTEND_URL

API_VERSION
```

Frontend

```text id="vgm4m3"
VITE_API_BASE_URL
```

Never commit `.env` files to Git.

---

# 5. Local Development

Backend

```bash id="gklr8p"
python -m venv .venv

source .venv/bin/activate

pip install -r requirements.txt

uvicorn app.main:app --reload
```

Frontend

```bash id="8b1sqb"
npm install

npm run dev
```

MongoDB

Use MongoDB Atlas or a local MongoDB instance.

---

# 6. Docker

Backend Dockerfile

Responsibilities

* Install dependencies
* Copy source code
* Expose API port
* Start FastAPI

Frontend Dockerfile (Optional)

Useful for local testing.

---

# 7. Docker Compose

Services

```text id="5h1ygt"
backend

frontend

mongodb (local only)

network
```

Example

```bash id="zyij4v"
docker compose up --build
```

Verify

* Frontend loads
* Backend responds
* Database connects
* APIs work

---

# 8. MongoDB Atlas

Steps

1. Create Atlas account.
2. Create cluster.
3. Create database user.
4. Configure network access.
5. Obtain connection string.
6. Store it in `MONGODB_URI`.

Verify backend connectivity before deployment.

---

# 9. Deploy Backend

Example using Railway

Steps

1. Push code to GitHub.
2. Create Railway project.
3. Connect repository.
4. Set environment variables.
5. Deploy.

Health endpoint

```text id="rf9g1d"
GET /health
```

Should return

```json id="ghs2lq"
{
  "status": "healthy"
}
```

---

# 10. Deploy Frontend

Example using Vercel

Steps

1. Import GitHub repository.
2. Select frontend directory.
3. Configure build settings.
4. Set `VITE_API_BASE_URL`.
5. Deploy.

Verify that the frontend can communicate with the backend.

---

# 11. Backend Configuration

Enable

* CORS
* HTTPS
* Environment validation
* Logging
* Compression (optional)

Disable

* Debug mode
* Detailed exception traces in production

---

# 12. Production Checklist

Before deployment verify:

* API keys configured
* MongoDB connection works
* JWT secret configured
* CORS configured
* HTTPS enabled
* Health endpoint works
* README updated
* Docker builds successfully
* No secrets committed

---

# 13. Monitoring

Track

* Application uptime
* API errors
* MongoDB connectivity
* AI provider failures
* Average response time
* Debate completion rate

Log

* Authentication events
* Debate creation
* AI API latency
* Unexpected exceptions

---

# 14. Error Recovery

If an AI provider fails

* Log the failure
* Retry if appropriate
* Return a friendly message
* Preserve debate state

If MongoDB fails

* Return HTTP 503
* Log the exception
* Do not expose internal details

---

# 15. Security

Always

* Hash passwords
* Validate all input
* Protect JWT secrets
* Use HTTPS
* Limit request sizes
* Configure CORS
* Sanitize user input

Never

* Expose API keys
* Store passwords in plain text
* Commit `.env` files
* Log sensitive credentials

---

# 16. CI/CD (Future)

Suggested workflow

```text id="pvxtg2"
Developer

↓

Git Push

↓

GitHub

↓

Run Tests

↓

Build Docker Image

↓

Deploy Backend

↓

Deploy Frontend
```

Potential tools

* GitHub Actions
* Railway Deployments
* Vercel Deployments

---

# 17. Scaling Strategy

Version 1

```text id="0fjkfh"
Frontend

↓

FastAPI

↓

MongoDB

↓

LLM APIs
```

Future

```text id="hkptio"
Load Balancer

↓

Multiple FastAPI Instances

↓

Redis Cache

↓

MongoDB Atlas

↓

Vector Database

↓

Multiple AI Providers
```

---

# 18. Backup Strategy

Database

* Enable MongoDB Atlas backups

Application

* GitHub repository
* Tagged releases
* Docker image versions

---

# 19. Release Process

Development

↓

Testing

↓

Staging (optional)

↓

Production

Every release should have:

* Version number
* Changelog
* Tested deployment

---

# 20. Production Validation

After deployment verify:

Authentication

* Register
* Login
* JWT validation

Debate

* Create debate
* Debate completes
* Messages saved
* History loads

Frontend

* Responsive
* No console errors
* Correct API URL

Backend

* Logs generated
* Health endpoint available
* No unhandled exceptions

Database

* Collections created
* Data persists
* Queries succeed

---

# 21. Version 2 Deployment

When RAG is introduced

Infrastructure becomes

```text id="xwgf4e"
React

↓

FastAPI

↓

MongoDB Atlas

↓

Vector Database

↓

OpenAI / Gemini

↓

Document Storage
```

---

# 22. Deployment Success Criteria

Deployment is considered successful when:

* Users can register and log in.
* Debates execute successfully.
* Messages persist in MongoDB.
* AI responses are returned reliably.
* The application is accessible through HTTPS.
* Docker containers build without errors.
* No sensitive information is exposed.
* The application can be updated with minimal downtime.

---

# Deployment Summary

## Hosting

Frontend

* Vercel

Backend

* Railway or Render

Database

* MongoDB Atlas

AI Providers

* OpenAI
* Gemini

Containerization

* Docker
* Docker Compose

Version Control

* GitHub

Monitoring

* Application logs
* Health endpoint
* Cloud platform metrics

The deployment architecture is designed to support a smooth transition from local development to a secure, scalable production environment while remaining simple enough for an individual developer to manage.
