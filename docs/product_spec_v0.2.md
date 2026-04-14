# Product Spec v0.2 - AI Student Assistant (Math-only Demo)

## Vision
Provide students a lightweight, deterministic math helper to practice solving arithmetic and quadratic equations. The app is demo-only; clearly marks "Demo mode (no real AI)".

## Core Flows
1. Register/Login with email + password.
2. Ask math question (arithmetic or quadratic) -> deterministic answer + 2-5 step explanation.
3. Save conversation to user history and display immediately.
4. View history list, open detail pages.
5. Handle backend errors with retry.

## Functional Requirements
- Auth: register, login, logout; JWT stored client-side (localStorage) for demo.
- Validation: question required, non-whitespace, max 300 chars.
- Ask endpoint saves Q&A per user with timestamps.
- History list searchable by question substring (client-side filter).
- Detail view shows question, answer, steps, created_at, and link to start new chat.
- Error states for timeouts/5xx with retry; empty state when no history.

## Non-Functional Requirements
- Deterministic math engine only (no external AI calls).
- Clear latency handling; optional artificial delay via env var.
- Responsive layout per wireframes; accessible form labels.
- Docker Compose brings up backend + Postgres.
- Environment variables documented via .env.example files.

## Data Model (Minimum)
- users(id, email unique, password_hash, created_at)
- conversations(id, user_id FK, question, answer, steps JSON/text, created_at)

## API Overview
- POST /api/auth/register {email, password}
- POST /api/auth/login -> {access_token}
- GET /api/auth/me -> {id, email}
- POST /api/qa/ask -> {id, question, answer, steps[], created_at}
- GET /api/qa/history -> list of {id, question_preview, created_at}
- GET /api/qa/history/{id} -> detail

## Constraints & Limitations
- Demo mode; no real AI; math-only.
- Token in localStorage (not production-safe).
- Single-node services; no scaling.

## Success Metrics
- Ability to complete US-01..US-05 manually.
- All pages reachable; history persists between sessions (same DB).
