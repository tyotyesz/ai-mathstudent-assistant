# AI Math Student Assistant

Prototype web application for math tutoring using a Qwen-based assistant. The app stores chat sessions per user, supports follow-up tutoring, and organizes saved chats into folders.

## Features
- Qwen-based math tutor with task generation, problem-solving hints, follow-up guidance, and non-math refusal behavior.
- Auth with JWT, profile view, password change modal, and account deletion.
- Chat history with completion status and folder organization.
- KaTeX math rendering on the frontend.

## Technology Stack
- Frontend: Next.js (App Router), TypeScript, Tailwind CSS, react-hot-toast, KaTeX.
- Backend: FastAPI, SQLAlchemy, JWT auth, Hugging Face Transformers (local Qwen model).
- Database: PostgreSQL (Docker Compose).

## Repository Structure
- backend/ - FastAPI app, SQLAlchemy models, Qwen tutor module.
- frontend/ - Next.js app, UI components, auth helpers.
- docs/ - Architecture, API, data model, requirements/scope, testing, and AI usage docs.
- tests/ - Acceptance test placeholders.

## Prerequisites
- Node.js 18+
- Python 3.11+
- Docker + Docker Compose
- Hugging Face token with access to `Qwen/Qwen2.5-Math-1.5B-Instruct`
- Free ports: 3000 (frontend), 8000 (backend), 5432 (Postgres)

## Environment Variables
Backend (see backend/.env.example):
- DATABASE_URL: SQLAlchemy connection string.
- SECRET_KEY: JWT signing key.
- ACCESS_TOKEN_EXPIRE_MINUTES: intended token expiry in minutes (login currently uses a fixed 60-minute expiry).
- ARTIFICIAL_LATENCY_MS: legacy artificial delay for the demo_math solver (not used by the Qwen tutor).
- HF_TOKEN: Hugging Face token used to download the model.
- QWEN_MODEL_ID: model identifier (default Qwen/Qwen2.5-Math-1.5B-Instruct).
- QWEN_MAX_NEW_TOKENS: generation cap for replies.
- QWEN_TEMPERATURE: sampling temperature.

Frontend (see frontend/.env.example):
- NEXT_PUBLIC_API_BASE: backend base URL (default http://localhost:8000).

Note: docker-compose.yml uses backend/.env.example by default. You can either edit backend/.env.example directly or create backend/.env and update docker-compose.yml to point env_file at backend/.env.

## Run with Docker Compose (DB + Backend)
1) Update backend/.env.example with your HF token and desired settings.
2) Start services:
   - docker-compose up --build
3) Backend runs at http://localhost:8000 and Postgres at port 5432.

GPU note: docker-compose.yml includes a GPU reservation block (for NVIDIA). If you do not have a GPU, Docker may ignore it, but CPU inference will be slow.

## Run Backend Locally (Optional)
1) Create and activate a Python 3.11+ virtual environment.
2) Install deps:
   - pip install -r backend/requirements.txt
3) Set environment variables (backend/.env or exported env vars).
4) Start server:
   - uvicorn app.main:app --reload --port 8000

## Run Frontend Locally
1) Set frontend/.env.example (or create frontend/.env) with NEXT_PUBLIC_API_BASE.
2) Start the app:
   - cd frontend
   - npm install
   - npm run dev
3) Open http://localhost:3000

## Database Notes
- PostgreSQL runs in Docker with volume db_data for persistence.
- Tables are created on backend startup via SQLAlchemy Base.metadata.create_all (no Alembic migrations in use).

## Hugging Face Token and Model Loading
- HF_TOKEN is required to download the Qwen model on first use.
- If HF_TOKEN is missing, the tutor replies with a configuration warning message.
- If model load fails (missing model files, memory, or other errors), the tutor replies with a temporary-unavailable message.
- The API still returns a normal 200 response; the failure is encoded in the assistant reply text.

## Demo Usage Flow
1) Register at /register and log in at /login.
2) On the home screen, start a new chat and ask a math question.
3) Continue with follow-up messages; the tutor returns only the next hint or step.
4) Try a non-math question (example: "Write me a poem") to see refusal behavior.
5) Create folders, move chats, and delete chats or folders (deleting a folder also deletes its chats).
6) Visit /profile to change password or delete the account.

## Known Limitations
- AI responses can be incorrect; results require verification.
- CPU inference is slow and memory-heavy; a GPU is recommended.
- Auth tokens are stored in localStorage (prototype only).
- No streaming responses or real-time typing indicators.
- No database migrations; schema changes require manual handling.
- Legacy deterministic solver exists in backend/core/demo_math.py for unit tests only; it is not used by the API.

## Troubleshooting
- 401 responses: re-login and confirm the token is stored in localStorage.
- Backend cannot connect to DB: ensure Docker is running and DATABASE_URL matches the db service name.
- Model download errors: verify HF_TOKEN and QWEN_MODEL_ID, then restart the backend.
- Very slow responses: reduce QWEN_MAX_NEW_TOKENS, lower QWEN_TEMPERATURE, or use a GPU.
- Frontend cannot reach backend: check NEXT_PUBLIC_API_BASE and CORS (port 3000).

For more details, see the documentation in docs/.
