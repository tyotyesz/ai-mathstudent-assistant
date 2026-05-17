# App Documentation - AI Math Student Assistant

This file is a short entry point for the project documentation. For detailed, up-to-date documents, see:

- docs/ARCHITECTURE.md
- docs/API.md
- docs/DATA_MODEL.md
- docs/AI_TUTOR.md
- docs/TESTING.md
- docs/AI_TUTOR_USAGE.md
- docs/REPRODUCTION.md
- docs/REQUIREMENTS_AND_SCOPE.md
- docs/ux/screens.md

## High-Level Summary
- Frontend: Next.js (App Router), TypeScript, Tailwind CSS, KaTeX rendering, JWT stored in localStorage.
- Backend: FastAPI with JWT auth, SQLAlchemy ORM, Qwen-based math tutor module.
- Database: PostgreSQL via Docker Compose, tables created at startup.
- Core flow: users register, log in, start a chat, and receive math-only tutor guidance with follow-up hints.

See the linked docs above for full details on architecture, API endpoints, and limitations.
