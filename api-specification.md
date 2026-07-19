# 03 - API Specification

# Project

**DebateAI - Multi-Agent AI Debate Platform**

Version: **1.0**

---

# 1. Overview

This document defines all REST APIs exposed by the DebateAI backend.

All communication between the frontend and backend occurs through these endpoints.

Base URL

```
http://localhost:8000/api/v1
```

Production

```
https://api.debateai.com/api/v1
```

---

# 2. API Design Principles

* RESTful APIs
* JSON Request & Response
* JWT Authentication
* Stateless Backend
* Versioned APIs
* Proper HTTP Status Codes
* Consistent Error Responses

---

# 3. Authentication

Authentication uses JWT Bearer Tokens.

Example Header

```
Authorization: Bearer <JWT_TOKEN>
```

Every protected endpoint requires this header.

---

# 4. Authentication APIs

---

## Register User

### Endpoint

```
POST /auth/register
```

### Request

```json
{
    "username":"hiruthick",
    "email":"hiruthick@gmail.com",
    "password":"Password@123"
}
```

### Response

```json
{
    "message":"User created successfully",
    "user_id":"..."
}
```

---

## Login

```
POST /auth/login
```

### Request

```json
{
    "email":"hiruthick@gmail.com",
    "password":"Password@123"
}
```

### Response

```json
{
    "access_token":"JWT_TOKEN",
    "token_type":"Bearer"
}
```

---

## Get Current User

```
GET /users/me
```

Response

```json
{
    "id":"...",
    "username":"hiruthick",
    "email":"hiruthick@gmail.com"
}
```

---

# 5. Debate APIs

---

## Create New Debate

```
POST /debates
```

### Request

```json
{
    "question":"Should AI replace doctors?",
    "rounds":2
}
```

---

### Backend Workflow

1. Validate JWT

2. Store debate

3. Call OpenAI

4. Call Gemini

5. Execute Debate

6. Generate Consensus

7. Store messages

8. Return response

---

### Response

```json
{
    "debate_id":"64abc...",
    "title":"Should AI replace doctors?",
    "status":"completed"
}
```

---

## Get All Debates

```
GET /debates
```

Returns

```json
[
   {
      "id":"...",
      "title":"AI vs Doctors",
      "updated_at":"..."
   }
]
```

---

## Get Debate By ID

```
GET /debates/{debate_id}
```

Returns

```json
{
    "debate":{
        ...
    },

    "messages":[
        ...
    ]
}
```

---

## Rename Debate

```
PUT /debates/{id}
```

Request

```json
{
   "title":"AI in Healthcare"
}
```

---

## Delete Debate

```
DELETE /debates/{id}
```

Response

```json
{
   "message":"Deleted"
}
```

---

# 6. Message APIs

---

## Get Debate Messages

```
GET /debates/{id}/messages
```

Returns

```json
[
   {
      "role":"user",
      "content":"..."
   },
   {
      "role":"openai",
      "content":"..."
   }
]
```

---

# 7. Debate Engine API

This endpoint executes the debate.

```
POST /debates/{id}/run
```

Normally called internally after debate creation.

---

Request

```json
{
    "rounds":2
}
```

---

Workflow

```
Question

↓

OpenAI

↓

Gemini

↓

Critique

↓

Critique

↓

Consensus
```

---

Response

```json
{
    "status":"completed"
}
```

---

# 8. Future Streaming API

Instead of waiting until the debate ends, responses can stream as they are generated.

```
GET /debates/{id}/stream
```

Technology

* Server-Sent Events (SSE)

or

* WebSockets

---

# 9. User APIs

---

## Update Profile

```
PUT /users/me
```

---

## Delete Account

```
DELETE /users/me
```

---

# 10. Health Check

```
GET /health
```

Response

```json
{
    "status":"healthy"
}
```

Useful for deployment monitoring.

---

# 11. Error Response Format

Every API returns the same error format.

```json
{
   "error":true,
   "message":"Invalid Token",
   "code":401
}
```

---

# 12. HTTP Status Codes

| Code | Meaning               |
| ---- | --------------------- |
| 200  | Success               |
| 201  | Created               |
| 400  | Bad Request           |
| 401  | Unauthorized          |
| 403  | Forbidden             |
| 404  | Not Found             |
| 409  | Conflict              |
| 422  | Validation Error      |
| 429  | Rate Limited          |
| 500  | Internal Server Error |

---

# 13. Validation Rules

Registration

* Username required
* Valid email
* Strong password

Debate

* Question cannot be empty
* Maximum length configurable
* Rounds between 1 and 5

---

# 14. API Rate Limits

Authenticated users

* 100 requests/hour (example)

Unauthenticated users

* Register/Login only

Future

Premium users

Higher limits

---

# 15. Security

* JWT Authentication
* bcrypt Password Hashing
* HTTPS
* Input Validation
* Request Size Limits
* CORS Protection

---

# 16. API Versioning

Current

```
/api/v1
```

Future

```
/api/v2
```

Allows introducing new features without breaking existing clients.

---

# 17. Request Lifecycle

```
React

↓

Axios

↓

FastAPI

↓

Authentication

↓

Debate Service

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

# 18. Future APIs

Version 2

```
POST /documents/upload

GET /documents

DELETE /documents
```

Version 3

```
POST /agents/create

GET /agents

DELETE /agents
```

Version 4

```
POST /strategies

GET /strategies
```

---

# 19. API Documentation

FastAPI automatically generates:

```
/docs
```

Swagger UI

and

```
/redoc
```

These will be available in both development and production (optionally restricted in production).

---

# 20. API Summary

Authentication

* POST /auth/register
* POST /auth/login
* GET /users/me

Debates

* POST /debates
* GET /debates
* GET /debates/{id}
* PUT /debates/{id}
* DELETE /debates/{id}

Messages

* GET /debates/{id}/messages

Engine

* POST /debates/{id}/run
* GET /debates/{id}/stream

System

* GET /health

The API is designed to be RESTful, modular, secure, and easily extensible. New AI providers, debate strategies, and features can be added without changing the existing API contract, ensuring long-term maintainability and scalability.
