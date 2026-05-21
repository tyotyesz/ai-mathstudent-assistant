# UX Screens and States

## Screen Overview

| ID | Screen | Purpose | Entry point | Auth required | Key interactions | Data source / API | Validation | Handled states |
|---|---|---|---|---|---|---|---|---|
| S01 | Login | Authenticates the user and opens access to the tutor workspace. | Public route or redirect from protected pages. | No | Enter email and password, submit login, navigate to registration. | `POST /api/auth/login` | Required fields, invalid credentials. | Idle, loading, error, successful redirect. |
| S02 | Register | Creates a new user account. | Registration link from the login screen. | No | Enter email and password, submit registration. | `POST /api/auth/register` | Required fields, password length, duplicate email. | Idle, loading, validation/API error, successful registration. |
| S03 | Main Chat Workspace | Provides the math tutor chat workspace with saved conversations and folders. | Default protected route after login. | Yes | Start chat, send follow-up message, select chat, create/delete folders (deleting a folder removes its chats), move chats, delete chats. | `GET /api/qa/chats`, `POST /api/qa/chats/start`, `POST /api/qa/chats/{chat_id}/messages`, `GET /api/qa/folders` | Non-empty message, backend max length handling. | Initial loading, empty chat panel, API error, successful chat messages. |
| S04 | Profile | Shows account details and account-related actions. | Header navigation / Profile link. | Yes | View profile, open password change modal, start account deletion, open saved chat. | `GET /api/auth/me`, `GET /api/qa/chats` | Redirect on auth failure. | Loading, empty saved chats, error, successful data display. |
| S05 | Change Password Modal | Updates the user's password. | Modal opened from the Profile screen. | Yes | Enter old/new password, save, cancel. | `PUT /api/auth/me/password` | Required fields, old and new password must differ, backend errors. | Idle, saving, error toast, successful close. |
| S06 | History Detail | Shows a read-only transcript of a saved chat. | Saved chat link, `/history/[id]` route. | Yes | View messages, return to Home. | `GET /api/qa/chats/{id}` | Missing or inaccessible chat handling. | Loading, not found, successful transcript. |
| S07 | Account Deletion Confirmation | Confirms irreversible account deletion. | Delete account button on Profile, browser confirmation. | Yes | Confirm or cancel deletion. | `DELETE /api/auth/me` | Confirmation required. | Confirm dialog, deleting, success redirect to Register/Login. |

## Screenshots

| Screen | Screenshot path | Note |
| --- | --- | --- |
| Login | docs/ux/screenshots/S01_bejelentkezes.png | Filename retains the original Hungarian label. |
| Register | docs/ux/screenshots/S02_regisztracio.png | Filename retains the original Hungarian label. |
| Main Chat Workspace | docs/ux/screenshots/S03_fooldal.png | Filename retains the original Hungarian label. |
| Profile | docs/ux/screenshots/S04_profil.png | Filename retains the original Hungarian label. |
| Change Password Modal | docs/ux/screenshots/S05_jelszomodositas.png | Filename retains the original Hungarian label. |