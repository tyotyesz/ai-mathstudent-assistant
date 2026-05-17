# Data Model

The backend uses SQLAlchemy ORM with PostgreSQL. Tables are created at startup.

## User
- Purpose: represents an authenticated user.
- Main fields:
  - id (UUID, primary key)
  - email (unique, indexed)
  - password_hash
  - created_at
- Relationships:
  - has many chats
  - has many folders

## Chat
- Purpose: a tutoring session that groups chat messages.
- Main fields:
  - id (UUID, primary key)
  - user_id (FK -> users.id)
  - folder_id (FK -> folders.id, nullable)
  - title (String, max 160)
  - is_completed (bool)
  - created_at
  - updated_at
- Relationships:
  - belongs to user
  - belongs to folder (optional)
  - has many chat_messages (ordered by created_at)

## ChatMessage
- Purpose: a single message within a chat session.
- Main fields:
  - id (UUID, primary key)
  - chat_id (FK -> chats.id)
  - role (user | assistant)
  - content (text)
  - category (task_generation | problem_solving | follow_up | non_math)
  - problem_completed (string: yes | no)
  - created_at
- Relationships:
  - belongs to chat
- Notes:
  - The API maps problem_completed to a boolean in responses.

## Folder
- Purpose: organize chats into groups.
- Main fields:
  - id (UUID, primary key)
  - user_id (FK -> users.id)
  - name (String, max 120)
  - created_at
- Relationships:
  - belongs to user
  - has many chats (cascade delete)
- Notes:
  - The ORM relationship is configured to delete chats when a folder is deleted.

## Conversation (Legacy)
- Purpose: legacy deterministic demo table (not used by current API/UI).
- Main fields:
  - id (UUID, primary key)
  - user_id (FK -> users.id)
  - question (text)
  - answer (text)
  - steps (text, JSON string)
  - created_at
- Note: present in the ORM model but not referenced by current endpoints.
