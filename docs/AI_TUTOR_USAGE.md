# AI Tutor Usage Statement and Evaluation Log

This document describes the AI usage inside the application, specifically the Qwen-based math tutor module. It does not describe AI tools used during thesis writing.

## AI Model Used
- Model: Qwen/Qwen2.5-Math-1.5B-Instruct
- Runtime: local Transformers inference (GPU if available, CPU fallback)

## Purpose of AI Usage
Provide math-only tutoring that emphasizes the next hint or step rather than full solutions.

## Prompt Strategy Summary
- System prompt enforces math-only scope and English-only responses.
- Task generation requests produce exactly one problem statement.
- Problem solving and follow-up requests produce a single next step.
- Non-math inputs are refused with a fixed message.

## Guardrails and Refusal Behavior
- Heuristic checks attempt to detect non-math inputs.
- Non-math requests return a refusal message.
- Requests for final answers are redirected to a single next step.

## Known Risks
- AI can hallucinate or provide incorrect guidance.
- Heuristic intent classification can misclassify edge cases.
- Long inputs may exceed model limits.

## Validation Approach
- Manual spot checks using a curated prompt set.
- Confirm refusal behavior on non-math prompts.
- Confirm tutoring style (one next step, no full solution).

## Limitations
- Not a replacement for expert instruction.
- No automated grading or correctness guarantees.
- Response quality varies with input clarity and model constraints.

## Future Improvements
- Automated evaluation suite with expected behaviors.
- Safer prompt parsing and stricter JSON validation.
- Model selection and configuration in admin settings.

## AI Evaluation Log

| Date | Evaluator | Prompt set | Summary | Result |
| --- | --- | --- | --- | --- |
| 2026-05-21 | Developer | Task generation | Checked whether the tutor returns one student-facing math problem without solution steps. | Passed |
| 2026-05-21 | Developer | Problem solving | Checked whether the tutor gives a next step or hint instead of a full solution. | Passed |
| 2026-05-21 | Developer | Follow-up and answer check | Checked follow-up behavior and answer-verification style. | Passed |
| 2026-05-21 | Developer | Non-math refusal | Checked whether non-math prompts are refused with a math-only response. | Passed |
| 2026-05-21 | Developer | Model unavailable case | Checked behavior when the model configuration is missing or unavailable. | Passed |