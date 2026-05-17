
# User Journeys

## 1. Fast access to the tutor workspace
Persona: a student who already has an account and wants to start tutoring quickly.

Entry point: Login page.

Steps:
1) Login (S01): user enters email and password, submits, and receives a token.
2) Home (S03): app loads folders and chats; user sees the chat workspace.
3) User starts a new chat and sends a math request.

Success criteria: user reaches the Home workspace and successfully sends the first message.

## 2. Start a new math chat and continue
Persona: a student who wants a new exercise and then follow-up hints.

Entry point: Home (S03).

Steps:
1) Start a chat with POST /api/qa/chats/start.
2) Receive the first assistant reply and see it in the chat panel.
3) Send follow-up messages via POST /api/qa/chats/{chat_id}/messages.
4) Optionally create a folder and move the chat into it.

Success criteria: at least one chat is created, stored, and reopened later.

## 3. Profile management (password change or account deletion)
Persona: a security-conscious user managing account settings.

Entry point: Profile (S04).

Steps:
1) Open profile and load email + saved chats.
2) Open the Change Password modal and submit new credentials.
3) Optionally delete the account and confirm the browser prompt.

Success criteria: password change succeeds or account deletion completes and logs the user out.
