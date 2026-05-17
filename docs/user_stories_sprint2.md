# User Stories Sprint 2 (Updated for Chat-Based Tutor)

## US-01 Empty state
- As a student, when I have no chats, I see a clear empty prompt that tells me to start a new math session.
- AC:
  - Home shows a prompt when no chat is selected.
  - Profile shows "No chats saved yet" when the list is empty.
  - State clears once at least one chat exists.

## US-02 Submit valid message
- As a student, I want validation preventing empty messages so I submit meaningful queries.
- AC:
  - Empty or whitespace-only messages are not submitted.
  - Submit button shows loading state while sending.
  - Backend enforces message length (max 600 chars).

## US-03 Receive tutor guidance
- As a student, I want concise tutor hints instead of a full solution.
- AC:
  - Assistant replies with the next step or hint.
  - Non-math inputs are refused with a math-only message.
  - Assistant labels indicate task generation, problem solving, follow-up, or refusal.

## US-04 View chat history and details
- As a student, I can browse saved chats and open the full transcript.
- AC:
  - Sidebar lists chats in most-recent order.
  - Selecting a chat loads messages.
  - History detail page shows a read-only transcript.

## US-05 Error handling
- As a student, when the service is unavailable, I see a clear error message and can retry manually.
- AC:
  - Failed requests show an error toast.
  - Re-sending the message succeeds once the backend is available.
