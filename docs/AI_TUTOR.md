# AI Tutor Module (Qwen)

## Model and Configuration
- Model: Qwen/Qwen2.5-Math-1.5B-Instruct (default).
- Config source: backend/app/core/config.py and backend/.env.example.
- Required environment variables:
  - HF_TOKEN: used to download model weights from Hugging Face.
  - QWEN_MODEL_ID: model identifier.
  - QWEN_MAX_NEW_TOKENS: max tokens per response.
  - QWEN_TEMPERATURE: sampling temperature.

## Model Loading
- The model is loaded locally using Transformers.
- If a GPU is available, 4-bit quantization is enabled via bitsandbytes.
- If no GPU is available, the model runs on CPU (slow, memory-heavy).

## System Prompt Purpose
The system prompt enforces:
- English-only responses.
- Math-only scope with refusal for non-math requests.
- Tutor-style guidance (next step or hint only).
- Task generation behavior (exactly one problem, no solution).
- JSON output preference with a fixed schema.

## Expected JSON Response Format
```
{
  "category": "task_generation" | "problem_solving" | "follow_up" | "non_math",
  "problem_completed": true | false,
  "reply": "string"
}
```
If JSON is not returned, the system attempts to recover a reply from raw text.

## Behavior by Intent

### Task Generation
- Triggered when the user asks to generate a new problem.
- Output should be a single math problem statement only.
- No solution steps or multiple problems.

### Problem Solving
- Triggered for direct solve requests.
- Output is the next step or hint, not the full solution.

### Follow-Up
- Triggered by requests like "next", "continue", or clarification questions.
- Output is a short, focused continuation of the previous step.

### Answer Check and Answer Requests
- If the user asks for the final answer, the tutor refuses to skip learning and gives one next step.
- If the user presents an answer attempt, the tutor verifies it when possible or asks for steps.

### Non-Math Refusal
- If the request is not math-related, the tutor returns a refusal message:
  - "This request is outside my scope. I can only help with mathematics-related questions and exercises."

## Failure Behavior
- Missing HF_TOKEN: reply indicates the model is not configured.
- Model load failure: reply indicates the tutor is temporarily unavailable.
- The API returns a normal 200 response; the failure is encoded in the reply text.

## Known Limitations
- Heuristic intent detection can misclassify inputs.
- The tutor does not guarantee correctness.
- Long or complex problems may exceed the model context or token cap.
- CPU inference is slow; GPU is recommended.

## Example Interactions

### Task generation
User: "Generate a quadratic equation problem."
Expected: single problem statement, no solution.

### Problem solving
User: "Solve x^2 - 5x + 6 = 0."
Expected: first hint (identify coefficients or discriminant).

### Answer check
User: "I got x = 2. Is that correct?"
Expected: confirm or ask for steps depending on the equation.

### Non-math refusal
User: "Write me a poem."
Expected: refusal message about math-only scope.
