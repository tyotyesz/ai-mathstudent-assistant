# AI Student Assistant (Qwen Math Tutor)

Monorepo implementing an AI-powered mathematics tutoring assistant using `Qwen/Qwen2.5-Math-1.5B-Instruct`. The app keeps chats per problem, supports follow-up tutoring, stores user chat history, and allows folder-based chat organization.

## Features
- US-01: Empty state when no history with CTA.
- US-02: Validate and submit non-empty, <300 char questions.
- US-03: Tutor-style, step-by-step guidance (next hint only; no full solution dump).
- US-04: List chats, open previous sessions, continue follow-up tutoring.
- US-05: Error state on backend timeout/5xx with retry.
- Folder management: create folders, move chats to folders, delete folders (with confirmation and cascade chat deletion).
- Profile management: show email, change password in modal, delete account.

## Stack
- Frontend: Next.js (App Router), TypeScript, Tailwind CSS, localStorage JWT, toast feedback.
- Backend: FastAPI, SQLAlchemy, JWT auth, password hashing, Qwen tutor integration via Hugging Face Inference API.
- DB: PostgreSQL (Docker Compose).

## Prerequisites
- Node.js 18+
- Python 3.11+
- Docker + Docker Compose
- Hugging Face API token with access to `Qwen/Qwen2.5-Math-1.5B-Instruct`
- Make sure ports 3000 (frontend), 8000 (backend), 5432 (Postgres) are free.

## Setup
1) Clone this repo and enter `app-project/`.
2) Start backend + DB:
   - `docker-compose up --build`
   - Backend runs on http://localhost:8000 , Postgres on 5432.
3) Backend env: copy `backend/.env.example` to `backend/.env` and set `HF_TOKEN`.
4) Frontend env: copy `frontend/.env.example` to `frontend/.env` and adjust API URL if needed.
5) Frontend install & run:
   - `cd frontend`
   - `npm install`
   - `npm run dev`
   - Visit http://localhost:3000

## Usage Flow
- Register at /register, then login at /login (or auto-redirect after register).
- Home (/): start a new chat or continue a selected chat.
- Ask for a new problem, solving help, or follow-up explanation.
- Tutor responds in English and only for mathematics-related requests.
- Folder actions: create folder, move chats, delete folder with confirmation.
- Profile shows saved chats, supports password change and account deletion.
- Logout clears token and redirects to /login.

## API Quick Overview
- POST /api/auth/register {email, password}
- POST /api/auth/login {email, password} -> {access_token}
- GET  /api/auth/me (JWT)
- PUT  /api/auth/me/password {old_password, new_password} (JWT)
- DELETE /api/auth/me (JWT)
- POST /api/qa/chats/start {message} (JWT)
- POST /api/qa/chats/{id}/messages {message} (JWT)
- GET  /api/qa/chats (JWT)
- GET  /api/qa/chats/{id} (JWT)
- DELETE /api/qa/chats/{id} (JWT)
- POST /api/qa/folders {name} (JWT)
- GET  /api/qa/folders (JWT)
- DELETE /api/qa/folders/{id} (JWT)
- PATCH /api/qa/chats/{id}/folder {folder_id|null} (JWT)

## Tests
- Backend unit test: deterministic solver.
- Acceptance test placeholders under tests/acceptance.

## Notes
- The tutor is mathematics-only and refuses out-of-scope requests.
- Responses are constrained to tutor-style guidance, not instant full solutions.
- Token is stored in localStorage (demo scope; not production-safe).
