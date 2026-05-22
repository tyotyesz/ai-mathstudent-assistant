# Reproduction Guide

This guide explains how to run the AI Math Student Assistant project locally for evaluation.

The project consists of:
- a Next.js frontend,
- a FastAPI backend,
- a PostgreSQL database,
- a Qwen-based AI math tutor module.

## 1) Clone the Repository

Run the following commands from the directory where you want to store the project:

```bash
git clone https://github.com/tyotyesz/ai-mathstudent-assistant.git
cd ai-mathstudent-assistant
```

## 2) Configure Environment Variables

### Backend environment

Docker Compose uses backend/.env by default. Create this file from the example file before starting the backend and database:

```bash
cp backend/.env.example backend/.env
```

Open backend/.env and set the required values.

At minimum, configure:

```env
HF_TOKEN=your_hugging_face_token
SECRET_KEY=your_long_random_secret_key
```

The `HF_TOKEN` is required for downloading or loading the Qwen model from Hugging Face.  
The `SECRET_KEY` is used by the backend for JWT authentication.

Other Qwen-related variables may also be configured, depending on the current env file, for example:

```env
QWEN_MODEL_ID=Qwen/Qwen2.5-Math-1.5B-Instruct
QWEN_MAX_NEW_TOKENS=...
QWEN_TEMPERATURE=...
```

Do not commit real secrets or tokens to the repository.

### Frontend environment

Create a frontend environment file from the example file:

```bash
cp frontend/.env.example frontend/.env
```

Open `frontend/.env` and check the backend API base URL. For local development, it should usually point to the FastAPI backend:

```env
NEXT_PUBLIC_API_BASE=http://localhost:8000
```

## 3) Start the Database and Backend

From the repository root, start the backend and database with Docker Compose:

```bash
docker-compose up --build
```

This should start:
- the PostgreSQL database,
- the FastAPI backend.

After the containers have started, verify that the backend is reachable:

```text
http://localhost:8000/health
```

Expected response:

```json
{"status":"ok"}
```

If the backend is not reachable, check the Docker logs and verify that the environment variables are correctly configured.

## 4) Start the Frontend

Open a new terminal window and run:

```bash
cd frontend
npm install
npm run dev
```

Then open the application in the browser:

```text
http://localhost:3000
```

## 5) Demo Flow

The following flow can be used to verify the main functionality of the application:

1. Open the frontend at `http://localhost:3000`.
2. Register a new account at `/register`.
3. Log in at `/login`.
4. Start a new chat from the main tutor workspace.
5. Send a math-related question.
6. Send a follow-up message in the same chat.
7. Verify that the conversation is saved.
8. Open a previous chat from the saved chat list or history view.
9. Create a folder and move a chat into it.
10. Delete a folder and confirm the chat is removed from the list.
11. Open `/profile`.
12. Verify that account-related functions are available, such as password change or account deletion.

## 6) Test Math Tutor Behavior

Use a simple math-related prompt, for example:

```text
Solve x^2 - 5x + 6 = 0.
```

Expected behavior:

- the system responds through the AI tutor module;
- the response should focus on math-related help;
- the response should support the learning process instead of acting as a general chatbot.

Depending on the current prompt configuration, the tutor may provide a hint, a next step, or a short guided explanation.

## 7) Test Non-Math Refusal

Send a non-math prompt, for example:

```text
Write me a poem.
```

Expected behavior:

- the assistant should refuse the request;
- the response should indicate that the application only supports mathematics-related questions and exercises.

## 8) Model Token or Model Loading Failure

If `HF_TOKEN` is missing, invalid, or the model cannot be loaded, the AI tutor may not be able to generate normal responses.

In this case, the evaluator can still verify:

- registration,
- login,
- JWT authentication,
- chat creation,
- chat persistence,
- folder handling,
- profile functions,
- frontend/backend communication.

However, AI response quality cannot be fully evaluated until the model configuration is fixed.

Check the backend logs if tutor responses fail.

## 9) Stop and Clean Up

To stop the running services:

```bash
docker-compose down
```

To remove containers and volumes:

```bash
docker-compose down -v
```

Use the volume removal command only if you also want to delete the local database data.

## 10) Troubleshooting

### Backend is not reachable

Check:

```text
http://localhost:8000/health
```

If it does not respond, verify that Docker Compose is running and check backend logs.

### Frontend cannot reach the backend

Verify the frontend environment variable:

```env
NEXT_PUBLIC_API_BASE=http://localhost:8000
```

Restart the frontend after changing `.env` values.

### Login or registration fails

Check that:

- the backend is running,
- the database container is running,
- the backend can connect to PostgreSQL,
- the request is sent to the correct API base URL.

### Tutor response fails

Check that:

- `HF_TOKEN` is set,
- the configured Qwen model ID is correct,
- the machine has enough memory,
- backend logs do not show model loading errors.

### Saved chats do not appear

Check that:

- the user is logged in,
- the JWT token is present,
- the backend can access the database,
- the chat creation endpoint completed successfully.
