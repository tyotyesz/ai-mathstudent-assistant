# User Stories Sprint 2

## US-01 Empty state
- As a student, when I have no history, I see an empty-state message with a CTA "Ask a question" to start my first conversation.
- AC:
  - Empty history list shows headline + description + CTA linking to ask form.
  - Appears on Home when no saved conversations.
  - Disappears once at least one item exists.
  - Suggested tests: load Home with no history -> empty panel visible; after first ask -> list populated.

## US-02 Submit valid question
- As a student, I want validation preventing empty/whitespace or overly long questions so I submit meaningful queries.
- AC:
  - Reject empty or whitespace-only input with inline error.
  - Reject >300 chars with inline error.
  - Submit button disabled while loading.
  - Suggested tests: submit whitespace -> error; submit 301 chars -> error; valid 20-char -> accepted.

## US-03 Get answer + steps
- As a student, I want to see an answer with short steps after loading.
- AC:
  - Loading indicator visible during request.
  - Response shows answer block and 2-5 bullet steps.
  - Toast indicates saved to history.
  - Suggested tests: valid ask -> loading -> answer + steps; history list updates.

## US-04 View history and details
- As a student, I can browse past conversations and open details.
- AC:
  - History sidebar shows latest first; filter/search by substring.
  - Clicking item opens /history/{id} showing Q, answer, steps, created_at.
  - "Start new chat" link goes to Home.
  - Suggested tests: create two asks -> history count 2; open first -> detail visible.

## US-05 Error + Retry
- As a student, when the service is unavailable or times out, I see an error panel with guidance and can retry.
- AC:
  - Backend 5xx/timeout shows error panel with message and prominent Retry button.
  - Retry resends last question; on success, error clears and answer shows.
  - Suggested tests: mock 500 -> error panel; click Retry -> success -> panel hidden.
