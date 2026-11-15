# AIQ Control Center — API Reference

Base URL: http://127.0.0.1:8000

## 1. Health
GET /health
Response: {"status": "ok", "database": "postgresql"}

## 2. Authentication
POST /auth/login
Body: {"username": "AIQ", "password": "..."}
Response: {"access_token": "...", "token_type": "bearer", "role": "founder"}

## 3. Review (requires Authorization: Bearer <token>)
GET /review/pending              — list pending approvals
GET /review/history              — list decided approvals
GET /review/task/{task_id}       — view task details
POST /review/{id}/decide         — approve / reject / request_changes
Body: {"decision": "approve", "reviewer_id": "...", "note": "..."}

## Security
- All /review/* endpoints require a valid token
- Only founder/reviewer roles can decide
- Tokens expire after 24 hours
- Passwords stored as PBKDF2-SHA256 hashes
