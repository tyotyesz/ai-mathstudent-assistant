# Testing and Validation

## Test Status Summary
| Area | Status | Evidence |
| --- | --- | --- |
| Backend unit tests (legacy demo_math) | Not executed yet | Tests exist under backend/tests/unit. |
| API manual validation | Not executed yet | Manual plan below. |
| Qwen tutor behavior checks | Not executed yet | AI validation table below. |

## Existing Tests

### Legacy Deterministic Solver (demo_math)
- backend/tests/unit/test_demo_math.py
  - Unit tests for the legacy deterministic solver. This solver is not used by the current API/UI.

### Acceptance Placeholders
- tests/acceptance/*.feature
  - Gherkin-style placeholders from the earlier demo flow (not aligned to the current chat-based tutor).

## How to Run Tests
Backend unit tests:
```
cd backend
pytest tests/unit
```

Note: There are no automated tests for the Qwen tutor module yet.

## Manual End-to-End Checklist
- [ ] Start Docker Compose (DB + backend).
- [ ] Confirm /health returns {"status":"ok"}.
- [ ] Start frontend and open http://localhost:3000.
- [ ] Register and log in.
- [ ] Start a new chat and receive an assistant reply.
- [ ] Send a follow-up message and receive a hint.
- [ ] Create a folder and move a chat into it.
- [ ] Delete the folder and confirm the chat is removed.
- [ ] Open /profile and change the password.
- [ ] Delete the account and confirm redirect to register/login.

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

### AI Validation Table (Not Executed Yet)
| Input prompt | Expected behavior | Validation criterion | Current result |
| --- | --- | --- | --- |
| "Generate an easy linear equation." | Return one problem statement only | Reply is a single problem, no solution | Not executed yet |
| "Solve x^2 - 5x + 6 = 0." | Provide a hint, not full solution | Reply contains a single next step | Not executed yet |
| "Just give me the final answer." | Refuse full solution | Reply gives one next step | Not executed yet |
| "I got x = 2. Is it correct?" | Check answer or ask for steps | Reply confirms or requests reasoning | Not executed yet |
| "Explain photosynthesis." | Refuse as non-math | Reply is math-only refusal | Not executed yet |
| "" (empty input) | Reject validation | API returns 422 validation error | Not executed yet |
| 700-character input | Reject validation | API returns 422 validation error | Not executed yet |
| Model unavailable (missing HF_TOKEN) | Return configuration warning | Reply indicates model not configured | Not executed yet |
