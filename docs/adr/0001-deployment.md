# ADR 0001 - Deployment Target

## Context
We need a simple deployment approach for a demo-grade AI Student Assistant. Requirements: fast setup, minimal ops, containerized services (backend + Postgres) and a static-ish frontend.

## Decision
Use Docker Compose for local/demo deployment. Backend (FastAPI) and Postgres run as services; frontend runs via `npm run dev` locally or can be containerized separately if needed.

## Consequences
- Pros: Simple, reproducible environment; aligns with demo scope.
- Cons: Not production-hardened; lacks scaling/monitoring.
- Notes: `.env.example` documents required variables. README provides "make it run" steps.
