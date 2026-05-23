# Testing and Validation

## Test Status Summary
| Area | Status | Evidence |
| --- | --- | --- |
| Backend unit tests (legacy demo_math) | Passed | Tests exist under backend/tests/unit. |
| API manual validation | Passed | Manual checklist executed below. |
| Qwen tutor behavior checks | Passed | AI validation table below. |

## Validation Environment

Manual validation date: 2026-05-21  
Environment: local development environment  
Backend: FastAPI started locally / through Docker Compose  
Database: PostgreSQL through Docker Compose  
Frontend: Next.js frontend on http://localhost:3000  
AI tutor: Qwen/Qwen2.5-Math-1.5B-Instruct through the backend tutor module  

Note: The Qwen tutor module does not currently have automated tests. Its behavior was validated manually through representative UI-based and API-based test cases.

## Existing Tests

### Legacy Deterministic Solver (demo_math)
- backend/tests/unit/test_demo_math.py
  - Unit tests for the legacy deterministic solver. This solver is not used by the current API/UI.

### Legacy Acceptance Files
- tests/acceptance/*.feature
  - Earlier Gherkin-style acceptance files from the initial demo flow.
  - These files are kept for documentation purposes, but they are not used as evidence for the current Qwen-based tutor validation.

## How to Run Tests
Backend unit tests:
```
cd backend
pytest tests/unit
```

Note: There are no automated tests for the Qwen tutor module yet.

## Manual End-to-End Checklist
- [x] Start Docker Compose (DB + backend).
- [x] Confirm /health returns {"status":"ok"}.
- [x] Start frontend and open http://localhost:3000.
- [x] Register and log in.
- [x] Start a new chat and receive an assistant reply.
- [x] Send a follow-up message and receive a hint.
- [x] Create a folder and move a chat into it.
- [x] Delete the folder and confirm the chat is removed.
- [x] Open /profile and change the password.
- [x] Delete the account and confirm redirect to register/login.

## Backend and API Validation Results
The backend and API endpoints were tested manually via FastAPI Swagger UI and frontend interactions. The results mirror the findings documented in the thesis (Figure 6.1.1).

| Date | Feature | Tested Behavior | Result |
| --- | --- | --- | --- |
| 2026-05-19 | Registration | Create a new user | Passed |
| 2026-05-19 | Login | Issue JWT token | Passed |
| 2026-05-19 | Start chat | Create a new conversation | Passed |
| 2026-05-19 | Send message | Save AI reply to database | Passed |
| 2026-05-19 | Folder management | Move chat into a folder | Passed |
| 2026-05-19 | Authorization | Prevent access to other users' chats | Passed |

## API Test Plan (Manual)
- Auth:
  - Register a new user.
  - Login and confirm a JWT is returned.
  - Access /api/auth/me with and without a token.
- Chat:
  - Start a chat.
  - Send follow-up messages.
  - List chats and open a chat by id.
  - Delete a chat.
- Folders:
  - Create a folder.
  - Move a chat into the folder.
  - Delete the folder and confirm chats are removed.

## Manual Test Cases
- Successful registration with valid email/password.
- Failed registration with existing email.
- Login success with correct credentials.
- Login failure with incorrect password.
- Protected endpoint access without token returns 401.
- Start chat and receive a tutor reply.
- Send follow-up message and receive a hint.
- Non-math prompt returns refusal.
- Folder creation, chat move, and folder deletion.
- Account deletion removes access and redirects to register.

## Negative Test Cases
- Empty message payload (expect 422 validation).
- Message longer than 600 characters (expect 422 validation).
- Invalid folder id during move (expect 404).
- Invalid chat id on fetch/delete (expect 404).
- Missing HF_TOKEN (expect tutor reply with configuration warning).
- Model load failure (expect tutor reply with temporary-unavailable message).

## AI Response Validation Plan
- Sample representative prompts each release.
- Verify refusal behavior for non-math inputs.
- Verify tutoring style (next step only).
- Verify JSON reply formatting is handled (or raw fallback is clean).

### AI Validation Table
The AI tutor's behavior was manually validated to ensure it acts as a tutor rather than a direct solver, and strictly adheres to the mathematics scope (as documented in Figure 6.3.1 of the thesis).

| Date | Input prompt / Test Case | Expected behavior | Current result |
| --- | --- | --- | --- |
| 2026-05-20 | "Generate an easy linear equation." (Task generation) | Return one specific math problem, no solution | Passed (manual) |
| 2026-05-20 | "Solve x^2 - 5x + 6 = 0." (Math question) | Provide a hint or next step, not full solution | Passed (manual) |
| 2026-05-20 | "Just give me the final answer." (Final answer request) | Refuse full solution, remain in tutor role | Passed (manual) |
| 2026-05-20 | "I got x = 2. Is it correct?" (Answer check) | Confirm answer or request steps/reasoning | Passed (manual) |
| 2026-05-20 | "Explain photosynthesis." (Non-math request) | Refuse request (Scope refusal) | Passed (manual) |
