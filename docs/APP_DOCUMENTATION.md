# App Documentation - AI Student Assistant (Demo)

## Architecture Overview
- Frontend: Next.js (App Router) + TypeScript + Tailwind. Stores JWT in localStorage (demo). Calls backend via REST.
- Backend: FastAPI with JWT auth, SQLAlchemy ORM, deterministic math solver. Persists conversations per user.
- Database: PostgreSQL (Docker Compose volume for persistence).
- Deployment: Docker Compose for backend + DB; frontend runs via npm dev. Future IaC planned (see ADRs).

## Routes & UI Behavior
- `/register`: Form to create account; on success redirects to `/login`.
- `/login`: Authenticates; on success stores JWT, shows toast, redirects to `/`.
- `/` (Home, guarded): Sidebar history + search; main ask form. Empty state when no history. Input validation (non-empty, <=300 chars). Loading indicator during request. Shows answer + steps and toast on success. Error panel with Retry on backend 5xx/timeout.
- `/profile` (guarded): History list ordered latest first; links to detail pages.
- `/history/[id]` (guarded): Shows question, answer, steps, created_at. "Start new chat" link to `/`.
- Top nav: Home, Profile, Logout (clears token, redirects to /login). Demo disclaimer visible.

## Data Model
- `users`: id (UUID), email (unique), password_hash, created_at.
- `conversations`: id (UUID), user_id FK, question text, answer text, steps JSON list, created_at.

## API Endpoints
- `POST /api/auth/register` {email, password} -> {id, email}
- `POST /api/auth/login` {email, password} -> {access_token}
- `GET /api/auth/me` (Bearer) -> {id, email}
- `POST /api/qa/ask` (Bearer) {question} -> {id, question, answer, steps[], created_at}
- `GET /api/qa/history` (Bearer) -> [{id, question_preview, created_at}]
- `GET /api/qa/history/{id}` (Bearer) -> {id, question, answer, steps[], created_at}

### Request/Response Examples
- Ask:
```
POST /api/qa/ask
Authorization: Bearer <token>
{
  "question": "x^2 - 5x + 6 = 0"
}
->
{
  "id": "...",
  "question": "x^2 - 5x + 6 = 0",
  "answer": "Roots: 2.0 and 3.0",
  "steps": ["Compute discriminant b^2-4ac = 1", "Roots = (5 ± 1)/2"],
  "created_at": "2025-01-30T12:00:00Z"
}
```

## Validation Rules
- Question required; trim whitespace; reject if empty.
- Max length 300 characters; inline error.
- Client disables submit while loading.

## Error Handling & Retry
- Backend 5xx or timeout triggers error panel with guidance and Retry button.
- Retry resends last question; on success clears error and shows answer.
- Toast feedback on success; inline errors for validation.

## Limitations
- Demo only: deterministic math helper (arithmetic + quadratics). No external AI/LLM.
- JWT stored in localStorage; not production-hardened.
- Simple Compose deployment; no scaling/monitoring.

## Deployment Notes
- See ADR 0001 (deployment) and ADR 0002 (IaC). Compose: `docker-compose up --build` for backend+DB. Frontend dev via `npm run dev`.
