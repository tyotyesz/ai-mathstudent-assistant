# Requirements and Scope - AI Math Student Assistant

## Target Users
- Students who want math practice with guided hints and follow-up tutoring.
- Reviewers evaluating a web-based AI tutor prototype in a thesis setting.

## Problem Statement
Students often need step-by-step guidance rather than full solutions. This prototype provides a math-only tutor that responds with the next hint or step while tracking conversation history per user.

## MVP Scope
A web-based prototype with authentication, chat-based tutoring, and basic content management for saved chats. The goal is reproducible evaluation rather than production-grade scale.

## Included in the Current Implementation
- Registration, login, profile, password change, and account deletion.
- Chat sessions with history and follow-up messaging.
- Folder creation and chat organization.
- Qwen-based math tutor with refusal behavior for non-math input.
- LaTeX/KaTeX rendering of math expressions.
- Docker Compose for local DB and backend.

## Explicitly Out of Scope
- Full curriculum management, grading, or learning analytics.
- Teacher dashboards or classroom management features.
- Multi-language tutoring.
- Mobile-native applications.
- Real-time collaboration or multiplayer sessions.
- Production security hardening, SSO, or advanced audit logging.

## Functional Requirements
- Users can register and log in with email and password.
- Authenticated users can start a new chat and continue follow-up messages.
- Each chat stores the full message history and completion status.
- Users can list, open, and delete chats.
- Users can create folders and move chats into folders.
- The tutor replies only to math-related input and refuses non-math requests.
- The frontend renders math expressions in tutor replies.

## Non-Functional Requirements
- Clear error handling for network and backend failures.
- Responsive layout for mobile and desktop.
- Configurable environment variables via .env.example files.
- Reproducible setup with Docker Compose.

## Known Limitations
- AI responses may be incorrect; results require verification.
- CPU inference is slow and memory-intensive.
- JWTs are stored in localStorage (prototype only).
- No DB migrations; schema is created at startup.
- No streaming responses or user-level rate limits.

## Future Improvements
- Streaming responses and richer tutor feedback.
- Automated evaluation harness for AI behavior.
- Optional model selection and caching of model weights.
- Accessibility improvements and more robust UX testing.
