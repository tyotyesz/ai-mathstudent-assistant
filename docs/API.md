# API Documentation

Base URL (local): http://localhost:8000

## Health
### GET /health
- Purpose: service health check.
- Auth: no.
- Response: {"status": "ok"}

## Authentication

### POST /api/auth/register
- Purpose: register a new user.
- Auth: no.
- Request body:
  - email (string, valid email)
  - password (string, 6-72 chars)
- Response: {"id": "...", "email": "..."}
- Errors: 400 (email already registered), 422 (validation errors).

### POST /api/auth/login
- Purpose: log in and get a JWT.
- Auth: no.
- Request body:
  - email (string)
  - password (string)
- Response: {"access_token": "...", "token_type": "bearer"}
- Errors: 401 (invalid credentials), 422 (validation errors).

### GET /api/auth/me
- Purpose: return the current user.
- Auth: Bearer token.
- Response: {"id": "...", "email": "..."}
- Errors: 401 (invalid or missing token).

### PUT /api/auth/me/password
- Purpose: change password.
- Auth: Bearer token.
- Request body:
  - old_password (string)
  - new_password (string, 6-72 chars)
- Response: 204 No Content.
- Errors: 400 (old password incorrect or same as new), 401 (invalid token), 422 (validation errors).

### DELETE /api/auth/me
- Purpose: delete the current account.
- Auth: Bearer token.
- Response: 204 No Content.
- Errors: 401 (invalid token).

## Chat and Tutor

### POST /api/qa/chats/start
- Purpose: create a new chat and get the first tutor reply.
- Auth: Bearer token.
- Request body:
  - message (string, 1-600 chars)
- Response: ChatResponse
- Errors: 401 (invalid token), 422 (validation errors).

### POST /api/qa/chats/{chat_id}/messages
- Purpose: send a follow-up message.
- Auth: Bearer token.
- Request body:
  - message (string, 1-600 chars)
- Response: ChatResponse
- Errors: 401 (invalid token), 404 (chat not found), 422 (validation errors).

### GET /api/qa/chats
- Purpose: list chats for the current user.
- Auth: Bearer token.
- Response: ChatListResponse

### GET /api/qa/chats/{chat_id}
- Purpose: get a full chat transcript.
- Auth: Bearer token.
- Response: ChatResponse
- Errors: 404 (chat not found).

### DELETE /api/qa/chats/{chat_id}
- Purpose: delete a chat.
- Auth: Bearer token.
- Response: 204 No Content.
- Errors: 404 (chat not found).

### PATCH /api/qa/chats/{chat_id}/folder
- Purpose: move a chat into a folder (or remove from folder).
- Auth: Bearer token.
- Request body:
  - folder_id (string | null)
- Response: ChatResponse
- Errors: 404 (chat not found, folder not found).

### GET /api/qa/history
- Purpose: legacy alias for chat listing.
- Auth: Bearer token.
- Response: ChatListResponse

## Folders

### POST /api/qa/folders
- Purpose: create a folder.
- Auth: Bearer token.
- Request body:
  - name (string, 1-120 chars)
- Response: FolderResponse
- Errors: 422 (validation errors).

### GET /api/qa/folders
- Purpose: list folders.
- Auth: Bearer token.
- Response: FolderListResponse

### DELETE /api/qa/folders/{folder_id}
- Purpose: delete a folder (and its chats).
- Auth: Bearer token.
- Response: 204 No Content.
- Errors: 404 (folder not found).

## Response Shapes

### ChatResponse
```
{
  "id": "uuid",
  "title": "string",
  "folder_id": "uuid|null",
  "is_completed": true,
  "created_at": "ISO-8601",
  "updated_at": "ISO-8601",
  "messages": [
    {
      "id": "uuid",
      "role": "user|assistant",
      "content": "string",
      "category": "task_generation|problem_solving|follow_up|non_math",
      "problem_completed": false,
      "created_at": "ISO-8601"
    }
  ]
}
```

### ChatListResponse
```
{
  "items": [
    {
      "id": "uuid",
      "title": "string",
      "folder_id": "uuid|null",
      "is_completed": false,
      "latest_preview": "string",
      "updated_at": "ISO-8601"
    }
  ]
}
```

### FolderResponse
```
{
  "id": "uuid",
  "name": "string",
  "chat_count": 0,
  "created_at": "ISO-8601"
}
```
