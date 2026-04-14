import json
import logging
import re
import threading
from typing import Dict, List

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

from app.core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

MATH_SCOPE_REFUSAL = "This request is outside my scope. I can only help with mathematics-related questions and exercises."

SYSTEM_PROMPT = """You are an English-only mathematics tutor assistant.
Follow all rules strictly:
1) You can only answer mathematics-related requests.
2) If a request is not mathematics-specific, return a refusal.
3) Tutor style only: do not reveal the full solution immediately.
4) For generation requests, create exactly one math exercise and ask the student to try first.
5) For solving requests and follow-up requests, provide only the next useful hint or step.
6) If the student reached the correct answer, confirm briefly and ask whether they want a deeper explanation.
7) Keep responses concise and in English.

Return ONLY valid JSON with this exact schema:
{
  "category": "task_generation" | "problem_solving" | "follow_up" | "non_math",
  "problem_completed": true | false,
  "reply": "string"
}
"""


def _looks_math_related(text: str) -> bool:
    lowered = text.lower()
    keywords = [
        "math", "algebra", "geometry", "calculus", "equation", "integral", "derivative",
        "quadratic", "function", "matrix", "probability", "statistics", "fraction", "number",
        "solve", "factor", "simplify", "limit", "trigonometry", "triangle", "circle",
    ]
    if any(word in lowered for word in keywords):
        return True
    if re.search(r"[0-9xyabc]\s*[\+\-\*/\^=]", lowered):
        return True
    if re.search(r"\b(sin|cos|tan|log|ln)\b", lowered):
        return True
    return False


def _safe_parse_json(raw: str) -> Dict[str, object]:
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", raw, flags=re.DOTALL)
        if not match:
            return {}
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            return {}


class QwenMathTutor:
    _lock = threading.Lock()
    _model = None
    _tokenizer = None
    _load_error = None

    def __init__(self) -> None:
        pass

    def _ensure_loaded(self) -> bool:
        if self.__class__._model is not None and self.__class__._tokenizer is not None:
            return True
        if self.__class__._load_error is not None:
            return False

        with self.__class__._lock:
            if self.__class__._model is not None and self.__class__._tokenizer is not None:
                return True
            if self.__class__._load_error is not None:
                return False

            try:
                tokenizer = AutoTokenizer.from_pretrained(
                    settings.qwen_model_id,
                    token=settings.hf_token or None,
                )

                if torch.cuda.is_available():
                    quantization_config = BitsAndBytesConfig(load_in_4bit=True)

                    model = AutoModelForCausalLM.from_pretrained(
                        settings.qwen_model_id,
                        token=settings.hf_token or None,
                        quantization_config=quantization_config,
                        device_map="auto",
                        dtype="auto",
                    )
                else:
                    model = AutoModelForCausalLM.from_pretrained(
                        settings.qwen_model_id,
                        token=settings.hf_token or None,
                        dtype=torch.float32,
                    )
                    model.to("cpu")

                if tokenizer.pad_token is None:
                    tokenizer.pad_token = tokenizer.eos_token

                self.__class__._tokenizer = tokenizer
                self.__class__._model = model
                return True

            except Exception as exc:
                self.__class__._load_error = exc
                logger.exception("Failed to load local Qwen model")
                return False

    def reply(self, history: List[Dict[str, str]], user_message: str) -> Dict[str, object]:
        history_context = " ".join(msg.get("content", "") for msg in history[-10:])
        if not _looks_math_related(user_message) and not _looks_math_related(history_context):
            return {
                "category": "non_math",
                "problem_completed": False,
                "reply": MATH_SCOPE_REFUSAL,
            }

        if not settings.hf_token:
            return {
                "category": "problem_solving",
                "problem_completed": False,
                "reply": "The math tutor model is not configured yet. Set HF_TOKEN on the backend to enable Qwen tutoring.",
            }

        if not self._ensure_loaded():
            return {
                "category": "problem_solving",
                "problem_completed": False,
                "reply": "The tutor service is temporarily unavailable. Please retry in a moment.",
            }

        history_lines = []
        for message in history[-12:]:
            role = message.get("role", "user")
            content = message.get("content", "")
            history_lines.append(f"{role.upper()}: {content}")

        try:
            tokenizer = self.__class__._tokenizer
            model = self.__class__._model
            messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": "Conversation so far:\n" + "\n".join(history_lines),
                },
                {"role": "user", "content": user_message},
            ]

            prompt_text = tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True,
            )
            inputs = tokenizer(prompt_text, return_tensors="pt")
            inputs = {key: value.to(model.device) for key, value in inputs.items()}

            with torch.no_grad():
                outputs = model.generate(
                    **inputs,
                    max_new_tokens=settings.qwen_max_new_tokens,
                    temperature=settings.qwen_temperature,
                    do_sample=settings.qwen_temperature > 0,
                    pad_token_id=tokenizer.pad_token_id,
                    eos_token_id=tokenizer.eos_token_id,
                )

            generated_tokens = outputs[0][inputs["input_ids"].shape[-1]:]
            raw = tokenizer.decode(generated_tokens, skip_special_tokens=True).strip()
            logger.warning("RAW MODEL OUTPUT: %s", raw)

        except Exception as e:
            logger.exception("Qwen inference failed")
            return {
                "category": "problem_solving",
                "problem_completed": False,
                "reply": f"The tutor service is temporarily unavailable. Please retry in a moment. Error: {e}",
            }

        parsed = _safe_parse_json(raw)
        logger.warning("PARSED JSON: %s", parsed)

        category = str(parsed.get("category", "problem_solving"))
        completed = bool(parsed.get("problem_completed", False))
        reply = str(parsed.get("reply", "")).strip()
        if not reply:
            reply = "Let's continue step by step. What have you tried so far?"

        if category == "non_math":
            reply = MATH_SCOPE_REFUSAL
            completed = False

        return {
            "category": category,
            "problem_completed": completed,
            "reply": reply,
        }


tutor = QwenMathTutor()
