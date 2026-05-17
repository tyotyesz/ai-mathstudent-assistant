import ast
import difflib
import json
import logging
import re
import threading
from typing import Dict, List, Optional, Tuple

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

When writing mathematical expressions, use LaTeX delimiters:
- Inline math: $...$
- Block math: $$...$$
Avoid \\( ... \\) and \\[ ... \\] if possible.
Do not output malformed or half-escaped LaTeX.

Prefer returning valid JSON with this exact schema:
{
    "category": "task_generation" | "problem_solving" | "follow_up" | "non_math",
    "problem_completed": true | false,
    "reply": "string"
}
If you cannot return JSON, return a plain English reply that follows the rules above.
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


def _strip_code_fences(text: str) -> str:
    fenced = re.match(r"^```(?:json)?\s*(.+?)\s*```$", text, flags=re.DOTALL | re.IGNORECASE)
    if fenced:
        return fenced.group(1).strip()
    return text


def _extract_first_json_object(text: str) -> str:
    start = text.find("{")
    if start == -1:
        return ""
    depth = 0
    for idx in range(start, len(text)):
        if text[idx] == "{":
            depth += 1
        elif text[idx] == "}":
            depth -= 1
            if depth == 0:
                return text[start:idx + 1]
    return ""


def _safe_parse_json(raw: str) -> Dict[str, object]:
    text = _strip_code_fences(raw.strip())
    if not text:
        return {}
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        candidate = _extract_first_json_object(text)
        if not candidate:
            return {}
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            return {}


def _clean_raw_answer(raw: str, user_message: str, history_lines: List[str]) -> str:
    cleaned = _strip_code_fences(raw).strip()
    if cleaned.startswith("\"") and cleaned.endswith("\""):
        try:
            cleaned = json.loads(cleaned)
        except json.JSONDecodeError:
            pass
    cleaned = str(cleaned).strip()
    cleaned = _strip_prompt_scaffolding(cleaned, user_message, history_lines)
    return cleaned.strip()


def _is_meaningful_text(text: str) -> bool:
    if not text:
        return False
    lowered = text.strip().lower()
    if lowered in {"null", "none", "{}", "[]"}:
        return False
    if not re.search(r"\w", lowered):
        return False
    return True


def _normalize_line(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def _strip_prompt_scaffolding(text: str, user_message: str, history_lines: List[str]) -> str:
    if not text:
        return text

    normalized_user = _normalize_line(user_message)
    skip_norms = set()
    for line in history_lines:
        norm_line = _normalize_line(line)
        if norm_line:
            skip_norms.add(norm_line)
        if ":" in line:
            content = line.split(":", 1)[1]
            norm_content = _normalize_line(content)
            if norm_content:
                skip_norms.add(norm_content)

    prompt_labels = {"user", "assistant", "system", "tutor"}
    prompt_markers = {"conversation so far", "current user message", "tutor instruction"}

    cleaned_lines = []
    for line in text.splitlines():
        raw_line = line.strip()
        if not raw_line:
            continue

        normalized = _normalize_line(raw_line)
        if normalized in skip_norms or normalized == normalized_user:
            continue
        if normalized in prompt_labels:
            continue

        marker_match = re.match(
            r"^(conversation so far|current user message|tutor instruction)\s*:\s*(.*)$",
            raw_line,
            flags=re.IGNORECASE,
        )
        if marker_match:
            remainder = marker_match.group(2).strip()
            if not remainder:
                continue
            raw_line = remainder
            normalized = _normalize_line(raw_line)
            if normalized in skip_norms or normalized == normalized_user:
                continue

        label_match = re.match(r"^(user|assistant|system|tutor)\s*:\s*(.*)$", raw_line, flags=re.IGNORECASE)
        if label_match:
            label = label_match.group(1).lower()
            remainder = label_match.group(2).strip()
            if label in {"user", "system"}:
                continue
            if not remainder:
                continue
            raw_line = remainder
            normalized = _normalize_line(raw_line)
            if normalized in skip_norms or normalized == normalized_user:
                continue

        cleaned_lines.append(raw_line)

    return "\n".join(cleaned_lines).strip()


def _is_answer_request(text: str) -> bool:
    lowered = text.lower()
    return bool(
        re.search(
            r"\b(tell me the answer|give me the answer|just give me the answer|what is the answer|i would be happy if you tell me the answer|can you just solve it|i want the final answer)\b",
            lowered,
        )
    )


def _is_answer_check(text: str) -> bool:
    lowered = text.lower().strip()
    if not lowered:
        return False
    if re.search(r"\b(is this correct|is that correct|is x =|is x=|is this right|was my answer good)\b", lowered):
        return True
    if re.search(r"\b(i got|i get|i think|my answer|my result|i found|i ended up with)\b", lowered):
        return True
    if re.search(r"\b(answer|result)\b", lowered) and re.search(r"\b(is|=)\b", lowered):
        return True
    if re.fullmatch(r"[-+]?\d+(?:\.\d+)?", lowered):
        return True
    if re.search(r"\b[a-z]\s*=\s*[-+]?\d+(?:\.\d+)?\b", lowered):
        return True
    return False


def _classify_intent(text: str, history_context: str) -> str:
    lowered = text.lower()
    if _is_answer_request(lowered):
        return "answer_request"
    if _is_answer_check(lowered):
        return "answer_check"
    if re.search(r"\b(generate|create|give|give me|make|compose|draft)\b", lowered) and re.search(
        r"\b(problem|exercise|task|question|equation)\b", lowered
    ):
        return "task_generation"
    if re.search(
        r"\b(then what should i do|what should i do next|what should i do|what next|next step|next|continue|can you explain|explain|give me a hint|hint|help me|help me understand|help|clarify|follow[- ]?up|why)\b",
        lowered,
    ):
        return "follow_up"
    if _looks_math_related(history_context) and re.search(r"\b(next|continue|then what)\b", lowered):
        return "follow_up"
    return "problem_solving"


def _is_missing_problem_request(text: str) -> bool:
    lowered = text.lower().strip()
    if not lowered:
        return False
    return bool(
        re.search(
            r"\b(i don't see the problem|i dont see the problem|where is the problem|there is no problem|can't see it|cant see it|what is the problem|missing problem)\b",
            lowered,
        )
    )


def _infer_completed(reply: str) -> bool:
    lowered = reply.lower()
    if re.search(r"\bfinal answer\b", lowered):
        return True
    if re.search(r"\bthe answer is\b", lowered):
        return True
    if re.search(r"\bsolution is\b", lowered):
        return True
    if "problem completed" in lowered:
        return True
    return False


def _user_provided_final_answer(user_message: str) -> bool:
    text = user_message.strip().lower()
    if not text:
        return False
    if re.search(
        r"\b(then what should i do|what should i do next|what should i do|what next|next|continue|can you explain|explain|give me a hint|hint|help me|help)\b",
        text,
    ):
        return False
    if re.search(r"\b(i got|i get|i think|i believe|my answer|my result|i found|i ended up with)\b", text):
        return True
    if re.search(r"\b(answer|result)\b", text) and re.search(r"\b(is|=)\b", text):
        return True
    if re.fullmatch(r"[-+]?\d+(?:\.\d+)?", text):
        return True
    if re.search(r"\b[a-z]\s*=\s*[-+]?\d+(?:\.\d+)?\b", text) and not re.search(
        r"\b(solve|find|simplify|compute|evaluate|determine|prove|show)\b",
        text,
    ):
        return True
    return False


def _assistant_confirms_correct(reply: str) -> bool:
    lowered = reply.lower()
    if re.search(r"\bthat(?:'s| is) correct\b", lowered):
        return True
    if re.search(r"\byou (?:are|re) correct\b", lowered):
        return True
    if re.search(r"\bthat's right\b", lowered) or re.search(r"\bthat is right\b", lowered):
        return True
    if re.search(r"\byou are right\b", lowered):
        return True
    if re.search(r"\byes,? that's right\b", lowered):
        return True
    if re.search(r"\bwell done\b", lowered) or re.search(r"\bnice work\b", lowered):
        return True
    if re.search(r"\bthat's the answer\b", lowered):
        return True
    if re.search(r"\bcorrect\b[.!?]", lowered) or re.fullmatch(r"correct[.!?]?", lowered.strip()):
        return True
    if re.search(r"\bexactly\b", lowered):
        return True
    return False


def _should_mark_completed(intent: str, user_message: str, reply: str) -> bool:
    if intent == "task_generation":
        return False
    if intent == "follow_up":
        return False
    if intent in {"answer_request", "answer_check"}:
        return False
    if not _user_provided_final_answer(user_message):
        return False
    return _assistant_confirms_correct(reply)


def _intent_instruction(intent: str) -> str:
    if intent == "answer_request":
        return (
            "The student asked for the answer. "
            "Acknowledge briefly and keep tutoring. "
            "Provide only ONE next step for the current problem. "
            "Do NOT give the full solution or multiple steps."
        )
    if intent == "answer_check":
        return (
            "The student provided an answer attempt. "
            "Check it if possible, otherwise ask for their reasoning. "
            "Keep the response short and tutor-focused."
        )
    if intent == "task_generation":
        return (
            "Output the actual problem statement directly. "
            "Do NOT output only an introduction line. "
            "Generate exactly ONE math problem. "
            "Do NOT include the solution, formulas, or derivations. "
            "Do NOT include multiple steps. "
            "Use simple problems if the user asks for easy difficulty. "
            "At most one short encouragement sentence is allowed."
        )
    if intent == "follow_up":
        return (
            "Continue from the last assistant step without repeating it. "
            "Provide only ONE short clarification or next hint. "
            "Do NOT restart the solution, and do NOT reveal the full solution or multiple steps. "
            "Do NOT use lists or say 'we will follow these steps'."
        )
    return (
        "Provide only the NEXT useful step or hint. "
        "Do NOT give a full derivation or multiple steps. "
        "Do NOT use lists or say 'we will follow these steps'. "
        "Do NOT give the final answer unless the student already reached it."
    )


def _clean_task_formatting(text: str) -> str:
    cleaned = re.sub(r"\\text\s*{([^}]*)}", r"\1", text)
    cleaned = re.sub(r"\\text\s*", "", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned.strip()


def _normalize_task_generation_text(text: str) -> str:
    if not text:
        return text
    normalized = text.replace("\r\n", "\n")
    normalized = normalized.replace("\\[", "")
    normalized = normalized.replace("\\]", "")
    normalized = normalized.replace("\\(", "")
    normalized = normalized.replace("\\)", "")
    normalized = normalized.replace("$$", "")
    normalized = re.sub(r"\\text\s*{([^}]*)}", r"\1", normalized)
    normalized = re.sub(r"\\text\s*", "", normalized)
    normalized = re.sub(r"\\quad", " ", normalized)
    normalized = re.sub(r"\\[,;:]", " ", normalized)
    normalized = re.sub(r"(?<![A-Za-z0-9])\{(?![A-Za-z0-9])", " ", normalized)
    normalized = re.sub(r"(?<![A-Za-z0-9])\}(?![A-Za-z0-9])", " ", normalized)
    normalized = re.sub(r"[ \t]+", " ", normalized)
    normalized = re.sub(r"\n\s*\n+", "\n", normalized)
    return normalized.strip()


def _is_meta_task_generation_reply(text: str) -> bool:
    lowered = text.strip().lower()
    if not lowered:
        return True
    return bool(
        re.match(
            r"^(let's start|we'll create|we will create|here's a problem statement|here is a problem statement|the user might want|this is straightforward|here is a simple problem|here is a simple mathematical problem|here is an easy mathematical problem|here is a mathematical problem|i will create)\b",
            lowered,
        )
    )


def _has_concrete_math_payload(text: str) -> bool:
    lowered = text.lower()
    if re.search(r"\b(f\(x\)\s*=)", lowered):
        return True
    if re.search(r"[0-9]", text) and re.search(r"[=\+\-*/\^]", text):
        return True
    if re.search(r"\b[a-z]\b", lowered) and re.search(r"[=\+\-*/\^]", text):
        return True
    if re.search(r"\b(integral|integrate|derivative|differentiate)\b", lowered) and re.search(r"[0-9a-z]", lowered):
        return True
    if re.search(r"\b(area|perimeter|triangle|circle|rectangle|probability|mean|median|variance|standard deviation)\b", lowered) and re.search(r"\b\d+\b", lowered):
        return True
    if re.search(r"\b(calculate|compute|simplify|evaluate|solve|find)\b", lowered) and re.search(r"\b\d+\b", lowered):
        return True
    return False


def _is_math_word(word: str) -> bool:
    return word.lower() in {"sin", "cos", "tan", "log", "ln", "sqrt", "exp", "pi", "e"}


def _trim_non_math_words(candidate: str) -> str:
    tokens = candidate.split()
    while tokens and re.fullmatch(r"[A-Za-z]+", tokens[0]) and not _is_math_word(tokens[0]) and len(tokens[0]) > 1:
        tokens = tokens[1:]
    while tokens and re.fullmatch(r"[A-Za-z]+", tokens[-1]) and not _is_math_word(tokens[-1]) and len(tokens[-1]) > 1:
        tokens = tokens[:-1]
    return " ".join(tokens)


def _is_equation_candidate(candidate: str) -> bool:
    if "=" not in candidate:
        return False
    if not re.search(r"[0-9A-Za-z]", candidate):
        return False
    for word in re.findall(r"[A-Za-z]+", candidate):
        if len(word) > 1 and not _is_math_word(word):
            return False
    parts = candidate.split("=")
    if len(parts) != 2:
        return False
    return all(re.search(r"[0-9A-Za-z]", part) for part in parts)


def _wrap_equations_in_dollars(text: str) -> str:
    if "$" in text:
        return text
    match = re.search(r"([0-9a-zA-Z\^\+\-*/\s\(\)]+=[0-9a-zA-Z\^\+\-*/\s\(\)]+)", text)
    if not match:
        return text
    candidate = match.group(1).strip()
    trimmed = _trim_non_math_words(candidate)
    if not trimmed or not _is_equation_candidate(trimmed):
        return text
    if trimmed not in text:
        return text
    return text.replace(trimmed, f"${trimmed}$", 1)


def _sanitize_task_reply(text: str) -> str:
    cleaned = _clean_task_formatting(text)
    return _wrap_equations_in_dollars(cleaned)


def _extract_problem_from_text(text: str) -> str:
    if not text:
        return ""
    cleaned = _clean_task_formatting(text)
    for match in re.findall(r"\$\$(.+?)\$\$", cleaned, flags=re.DOTALL):
        if _contains_problem_statement(match):
            return match.strip()
    for match in re.findall(r"\$(.+?)\$", cleaned, flags=re.DOTALL):
        if _contains_problem_statement(match):
            return match.strip()
    equation_match = re.search(r"([0-9a-zA-Z\^\+\-*/\s\(\)]+=[0-9a-zA-Z\^\+\-*/\s\(\)]+)", cleaned)
    if equation_match:
        return equation_match.group(1).strip()
    func_match = re.search(r"f\(x\)\s*=\s*[^.]+", cleaned)
    if func_match:
        return func_match.group(0).strip()
    if re.search(r"\b(rectangle|triangle|circle|area|perimeter|probability|mean|median|variance)\b", cleaned.lower()):
        return cleaned.strip()
    return ""


def _extract_current_problem(history: List[Dict[str, str]], user_message: str) -> str:
    candidates = []
    if user_message:
        candidates.append(user_message)
    for message in reversed(history[-20:]):
        candidates.append(message.get("content", ""))
    for candidate in candidates:
        extracted = _extract_problem_from_text(candidate)
        if extracted:
            return extracted
    return ""


def _looks_like_new_problem_request(text: str) -> bool:
    lowered = text.lower()
    if re.search(
        r"\b(solve|find|compute|determine|evaluate|simplify|factor|expand|differentiate|integrate|prove|show|calculate|derivative|integral)\b",
        lowered,
    ):
        return True
    if re.search(r"\b(rectangle|triangle|circle|area|perimeter|probability|mean|median|variance|standard deviation)\b", lowered):
        return True
    if re.search(r"[0-9]", lowered) and re.search(r"[=\+\-*/\^]", lowered):
        return True
    return False


def _extract_current_problem_by_intent(
    history: List[Dict[str, str]],
    user_message: str,
    intent: str,
) -> str:
    if intent in {"answer_check", "answer_request", "follow_up"}:
        extracted = _extract_current_problem(history, "")
        if extracted:
            return extracted
        if _looks_like_new_problem_request(user_message):
            return _extract_problem_from_text(user_message)
        return ""

    if _looks_like_new_problem_request(user_message) or _contains_problem_statement(user_message):
        extracted = _extract_problem_from_text(user_message)
        if extracted:
            return extracted
    return _extract_current_problem(history, "")


def _detect_problem_type(problem_text: str) -> str:
    if not problem_text:
        return "unknown_math"
    lowered = problem_text.lower()
    if re.search(r"\b(integral|integrate|int)\b", lowered):
        return "calculus_integral"
    if re.search(r"\b(derivative|differentiate|d/dx|f'\(x\))\b", lowered):
        return "calculus_derivative"
    if re.search(r"\b(probability|chance|dice|balls|cards|bag)\b", lowered):
        return "probability"
    if re.search(r"\b(mean|median|variance|standard deviation|std)\b", lowered):
        return "statistics"
    if re.search(r"\b(area|perimeter|triangle|circle|rectangle|volume)\b", lowered):
        return "geometry"
    if re.search(r"\b(simplify|factor|expand)\b", lowered):
        return "simplification"
    if "=" not in lowered and re.search(r"\b[a-z]\b", lowered) and re.search(r"[\+\-*/\^]", lowered):
        return "simplification"
    if re.search(r"\b[a-z]\s*(\^|\*\*)\s*2\b", lowered) and "=" in lowered:
        return "quadratic_equation"
    if "=" in lowered and re.search(r"\b[a-z]\b", lowered):
        return "linear_equation"
    if re.fullmatch(r"[0-9\s\+\-*/\^\(\)=.]+", problem_text.strip()):
        return "arithmetic"
    if re.search(r"\b(function|f\(x\))\b", lowered):
        return "function"
    if re.search(r"\b(there are|a bag|a box|a person|a train|a car)\b", lowered):
        return "word_problem"
    return "unknown_math"


def _format_problem_text(problem_text: str) -> str:
    if not problem_text:
        return ""
    if "$" in problem_text:
        return problem_text
    if re.fullmatch(r"[0-9a-zA-Z\^\+\-*/\s\(\)=.]+", problem_text.strip()):
        return f"${problem_text}$"
    return problem_text


def _next_step_hint(problem_type: str, last_assistant: str, history_context: str, problem_text: str) -> str:
    lowered = last_assistant.lower()
    formatted_problem = _format_problem_text(problem_text)
    if problem_type == "quadratic_equation":
        if "discriminant" in lowered or "d =" in lowered:
            return "Now apply the quadratic formula. What expression do you get for $x$?"
        if "quadratic formula" in lowered:
            return "Substitute the values for $a$, $b$, and $c$ and simplify. What do you get?"
        if "a =" in lowered or "b =" in lowered or "c =" in lowered or "coeff" in lowered:
            return "Now compute the discriminant using $D = b^2 - 4ac$. What value do you get?"
        return f"First, identify the coefficients in {formatted_problem}: what are $a$, $b$, and $c$?"
    if problem_type == "linear_equation":
        if "combine" in lowered or "simplify" in lowered:
            return "Next, move the constant term to the other side. What equation do you get?"
        if "move" in lowered or "subtract" in lowered:
            return "Now divide both sides by the coefficient of $x$. What is $x$?"
        if "=" in history_context:
            return "First, combine like terms on one side of the equation. What equation do you get?"
        return "Isolate the variable by moving constants to the other side. What do you get?"
    if problem_type == "simplification":
        if "distribute" in lowered or "expand" in lowered:
            return "Now combine like terms to simplify the expression. What do you get?"
        return "First, distribute or expand the expression. What does it become?"
    if problem_type == "arithmetic":
        return "Compute the next operation in the expression. What value do you get?"
    if problem_type == "geometry":
        return "Identify the relevant formula and plug in the given values. What do you get?"
    if problem_type == "probability":
        return "Count favorable outcomes and total outcomes, then form the ratio. What do you get?"
    if problem_type == "statistics":
        return "List the data and apply the appropriate formula. What do you get?"
    if problem_type == "calculus_derivative":
        return "Identify the differentiation rule and differentiate term by term. What do you get?"
    if problem_type == "calculus_integral":
        return "Identify the integration rule and integrate term by term. What do you get?"
    if problem_type == "function":
        return "Write the function clearly and substitute the requested input. What do you get?"
    if problem_type == "word_problem":
        return "Extract the known values and define the unknown. What equation can you set up?"
    if "=" in history_context:
        return "First, combine like terms on one side of the equation. What equation do you get?"
    return "Take the next algebraic step and tell me the result."


def _answer_request_reply(problem_type: str, last_assistant: str, history_context: str, problem_text: str) -> str:
    boundary = "I can help you get there, but I will not skip the learning step. "
    step = _next_step_hint(problem_type, last_assistant, history_context, problem_text)
    return boundary + step


def _safe_eval_arithmetic(expr: str) -> Optional[float]:
    expr = expr.replace("^", "**")
    try:
        parsed = ast.parse(expr, mode="eval")
    except SyntaxError:
        return None
    for node in ast.walk(parsed):
        if not isinstance(
            node,
            (
                ast.Expression,
                ast.BinOp,
                ast.UnaryOp,
                ast.Add,
                ast.Sub,
                ast.Mult,
                ast.Div,
                ast.Pow,
                ast.USub,
                ast.UAdd,
                ast.Load,
                ast.Constant,
                ast.Mod,
                ast.FloorDiv,
            ),
        ):
            return None
        if isinstance(node, ast.Constant) and not isinstance(node.value, (int, float)):
            return None
    try:
        return float(eval(compile(parsed, "<expr>", "eval"), {"__builtins__": {}}))
    except Exception:
        return None


def _extract_answer_attempt(text: str) -> Optional[float]:
    match = re.search(r"[-+]?\d+(?:\.\d+)?", text)
    if not match:
        return None
    try:
        return float(match.group(0))
    except ValueError:
        return None


def _parse_linear_equation(problem_text: str) -> Optional[Tuple[float, float, float]]:
    expr = problem_text.replace(" ", "")
    match = re.match(r"^([+-]?\d*\.?\d*)x([+-]\d*\.?\d*)?=([+-]?\d*\.?\d*)$", expr)
    if not match:
        return None
    a_str, b_str, c_str = match.group(1), match.group(2), match.group(3)
    if a_str in {"", "+"}:
        a = 1.0
    elif a_str == "-":
        a = -1.0
    else:
        a = float(a_str)
    b = float(b_str) if b_str else 0.0
    c = float(c_str)
    return a, b, c


def _parse_quadratic_equation(problem_text: str) -> Optional[Tuple[float, float, float]]:
    expr = problem_text.replace(" ", "")
    match = re.match(r"^([+-]?\d*\.?\d*)x\^2([+-]\d*\.?\d*)x([+-]\d*\.?\d*)=0$", expr)
    if not match:
        return None
    a_str, b_str, c_str = match.group(1), match.group(2), match.group(3)
    a = 1.0 if a_str in {"", "+"} else (-1.0 if a_str == "-" else float(a_str))
    b = float(b_str)
    c = float(c_str)
    return a, b, c


def _check_answer(problem_type: str, problem_text: str, answer_value: float) -> Optional[bool]:
    if problem_type == "arithmetic":
        expr_match = re.search(r"([0-9\s\+\-*/\^\(\)\.]+)", problem_text)
        if not expr_match:
            return None
        value = _safe_eval_arithmetic(expr_match.group(1))
        if value is None:
            return None
        return abs(value - answer_value) < 1e-6
    if problem_type == "linear_equation":
        parsed = _parse_linear_equation(problem_text)
        if not parsed:
            return None
        a, b, c = parsed
        if a == 0:
            return None
        expected = (c - b) / a
        return abs(expected - answer_value) < 1e-6
    if problem_type == "quadratic_equation":
        parsed = _parse_quadratic_equation(problem_text)
        if not parsed:
            return None
        a, b, c = parsed
        value = a * answer_value * answer_value + b * answer_value + c
        return abs(value) < 1e-6
    return None


def _answer_check_reply(problem_type: str, problem_text: str, user_message: str, last_assistant: str, history_context: str) -> str:
    answer_value = _extract_answer_attempt(user_message)
    if answer_value is None:
        return "I can check it if you share the numeric answer you got."
    verdict = _check_answer(problem_type, problem_text, answer_value)
    if verdict is True:
        return "That looks correct. Do you want a brief explanation of why?"
    if verdict is False:
        return "Not quite. Try the next step again, and tell me what you get."
    return "I cannot verify that directly. Show your steps or tell me the equation you reached."


def _normalize_for_similarity(text: str) -> str:
    lowered = text.lower()
    return re.sub(r"[^a-z0-9]+", "", lowered)


def _is_repeated_reply(candidate: str, previous: str) -> bool:
    if not previous or not candidate:
        return False
    if len(candidate.strip()) < 12:
        return False
    norm_candidate = _normalize_for_similarity(candidate)
    norm_previous = _normalize_for_similarity(previous)
    if not norm_candidate or not norm_previous:
        return False
    if norm_candidate == norm_previous:
        return True
    ratio = difflib.SequenceMatcher(a=norm_candidate, b=norm_previous).ratio()
    return ratio >= 0.9


def _fallback_follow_up_hint(
    last_assistant: str,
    history_context: str,
    problem_type: str,
    problem_text: str,
) -> str:
    return _next_step_hint(problem_type, last_assistant, history_context, problem_text)


def _contains_problem_statement(text: str) -> bool:
    lowered = text.lower()
    if re.search(
        r"\b(solve|find|compute|determine|evaluate|simplify|factor|expand|differentiate|integrate|prove|show|calculate|derivative|integral|probability|mean|median|variance|standard deviation)\b",
        lowered,
    ):
        return True
    if re.search(r"[0-9]", text) and re.search(r"[=\+\-*/\^]", text):
        return True
    if re.search(r"\b(x|y|z|n|k)\b", lowered) and re.search(r"[=\+\-*/\^]", text):
        return True
    if re.search(r"\b(rectangle|triangle|circle|area|perimeter|probability|function|equation)\b", lowered):
        return True
    return False


def _looks_intro_only(text: str) -> bool:
    lowered = text.strip().lower()
    if not lowered:
        return True
    if re.match(
        r"^(here is|here's|try this|problem:|here is a problem|here is a mathematical problem|here is an easy problem|here is an easy mathematical problem|here is an advanced problem|here is an advanced mathematical problem)\b",
        lowered,
    ):
        return True
    if lowered.endswith(":"):
        return True
    return False


def _fallback_problem(user_message: str) -> str:
    logger.warning("USING_FALLBACK_TASK_GENERATION")
    lowered = user_message.lower()
    if "probability" in lowered or "chance" in lowered or "dice" in lowered or "balls" in lowered or "cards" in lowered:
        problem = "A bag contains 3 red balls and 2 blue balls. What is the probability of drawing a red ball?"
    elif "statistics" in lowered or "mean" in lowered or "median" in lowered or "variance" in lowered or "standard deviation" in lowered:
        problem = "Find the mean of 4, 7, 9, and 10."
    elif "derivative" in lowered or "differentiate" in lowered or "calculus" in lowered:
        problem = "Find the derivative of $f(x) = x^3 - 4x$."
    elif "integral" in lowered or "integrate" in lowered:
        problem = "Evaluate the integral $\\int 2x\\,dx$."
    elif "geometry" in lowered or "rectangle" in lowered or "area" in lowered or "perimeter" in lowered or "triangle" in lowered:
        problem = "A rectangle has length $8$ and width $5$. What is its area?"
    elif "function" in lowered:
        problem = "Evaluate $f(x) = x^2 - 3x$ at $x = 2$."
    elif "simplify" in lowered or "factor" in lowered or "expand" in lowered:
        problem = "Simplify the expression $2(x + 3) - 4$."
    elif "quadratic" in lowered or "advanced" in lowered:
        problem = "Solve the equation $2x^2 + 3x - 2 = 0$ for $x$."
    elif "linear" in lowered or "equation" in lowered:
        problem = "Solve the equation $3x + 4 = 16$."
    elif "arithmetic" in lowered or "easy" in lowered:
        problem = "Calculate: $8 + 7 - 3$."
    elif "word" in lowered or "story" in lowered:
        problem = "A car travels 60 km in 1.5 hours. What is its average speed?"
    else:
        problem = "Solve the equation $3x + 4 = 16$."
    return f"{problem} Try solving it first, and I can help step by step."


def _ensure_task_problem(reply: str, user_message: str) -> str:
    cleaned = reply.strip()
    if not _is_meaningful_text(cleaned):
        return _fallback_problem(user_message)
    if _is_meta_task_generation_reply(cleaned):
        return _fallback_problem(user_message)
    if _looks_intro_only(cleaned):
        return _fallback_problem(user_message)
    if not _has_concrete_math_payload(cleaned):
        return _fallback_problem(user_message)
    return cleaned


def _looks_generic_intro(text: str) -> bool:
    lowered = text.strip().lower()
    if not lowered:
        return True
    if re.match(r"^(let's|let us|we will|we'll) (solve|work|start|go)\b", lowered):
        return True
    if re.search(r"we will follow these steps", lowered):
        return True
    if re.match(r"^to solve the equation\b", lowered):
        return True
    return False


def _ends_with_unfinished_list(text: str) -> bool:
    lowered = text.rstrip().lower()
    if re.search(r"\bstep\s*1\s*:\s*$", lowered):
        return True
    if re.search(r"\bsteps?\s*:\s*$", lowered):
        return True
    if re.search(r"\b1\s*[\.)]\s*$", lowered):
        return True
    return False


def _strip_unfinished_list(text: str) -> str:
    cleaned = re.sub(r"\bstep\s*1\s*:\s*$", "", text, flags=re.IGNORECASE).rstrip()
    cleaned = re.sub(r"\bsteps?\s*:\s*$", "", cleaned, flags=re.IGNORECASE).rstrip()
    cleaned = re.sub(r"\b1\s*[\.)]\s*$", "", cleaned).rstrip()
    return cleaned


def _strip_trailing_colon(text: str) -> str:
    if text.rstrip().endswith(":"):
        return text.rstrip()[:-1].rstrip()
    return text


def _reduce_multiple_steps(text: str) -> str:
    lowered = text.lower()
    if " then " in lowered:
        parts = re.split(r"\bthen\b", text, maxsplit=1, flags=re.IGNORECASE)
        return parts[0].strip().rstrip(",")
    if " and then " in lowered:
        parts = re.split(r"\band then\b", text, maxsplit=1, flags=re.IGNORECASE)
        return parts[0].strip().rstrip(",")
    if ";" in text:
        return text.split(";", 1)[0].strip()
    return text


def _finalize_step_reply(
    intent: str,
    reply: str,
    last_assistant: str,
    history_context: str,
    problem_type: str,
    problem_text: str,
) -> str:
    cleaned = reply.strip()
    if intent not in {"problem_solving", "follow_up", "answer_request", "answer_check"}:
        return cleaned

    cleaned = _clean_task_formatting(cleaned)
    if _ends_with_unfinished_list(cleaned):
        cleaned = _strip_unfinished_list(cleaned)
    cleaned = _strip_trailing_colon(cleaned)
    cleaned = _reduce_multiple_steps(cleaned)

    linear_hint = re.search(
        r"\b(combine like terms|subtract the constant term|isolate the variable|move the constant|divide both sides)\b",
        cleaned.lower(),
    )
    if problem_type in {"quadratic_equation", "probability", "statistics", "geometry", "calculus_derivative", "calculus_integral", "function", "word_problem", "arithmetic"} and linear_hint:
        return _next_step_hint(problem_type, last_assistant, history_context, problem_text)

    if _looks_generic_intro(cleaned):
        return _next_step_hint(problem_type, last_assistant, history_context, problem_text)
    if _is_repeated_reply(cleaned, last_assistant):
        return _next_step_hint(problem_type, last_assistant, history_context, problem_text)
    if not _is_meaningful_text(cleaned):
        return _next_step_hint(problem_type, last_assistant, history_context, problem_text)

    return cleaned


def _trim_to_single_step(reply: str) -> str:
    cleaned = reply.strip()
    if not cleaned:
        return cleaned
    parts = re.split(r"(?<=[.!?])\s+", cleaned)
    if len(parts) <= 1:
        return cleaned
    first = parts[0].strip()
    second = parts[1].strip() if len(parts) > 1 else ""
    if second.endswith("?") and len(second) <= 120:
        return f"{first} {second}".strip()
    return first


def _trim_task_generation_reply(reply: str) -> str:
    cleaned = reply.strip()
    if not cleaned:
        return cleaned
    solution_cutoff = re.search(
        r"(?:\blet's solve\b|\blet us solve\b|\bwe can solve\b|\bwe will solve\b|"
        r"\bstep[-\s]*by[-\s]*step\b|\bsolution\b\s*[:\-]|\banswer\b\s*[:\-]|"
        r"\bexplanation\b\s*[:\-]|\bsteps?\b\s*[:\-]|\bstep\s*\d+\b|"
        r"^\s*\d+\s*[\.)]|\bfirst,\s*subtract\b|\bnow\s*subtract\b|\btherefore\b|\bthus\b)",
        cleaned,
        flags=re.IGNORECASE | re.MULTILINE,
    )
    if solution_cutoff:
        cleaned = cleaned[: solution_cutoff.start()].strip()
    marker_match = re.search(r"\b(solution|answer|steps|explanation|derivation|hint)\b\s*[:\-]", cleaned, re.IGNORECASE)
    if marker_match:
        cleaned = cleaned[: marker_match.start()].strip()

    lines = [line.strip() for line in cleaned.splitlines() if line.strip()]
    if not lines:
        return cleaned

    def _is_problem_marker(line: str) -> bool:
        return bool(
            re.match(
                r"^\*{0,2}\s*(problem|exercise|task|question)\s*[:\-]",
                line.strip(),
                re.IGNORECASE,
            )
        )

    def _is_solution_marker(line: str) -> bool:
        return bool(
            re.match(
                r"^\*{0,2}\s*(solution|answer|explanation|steps?|hint|derivation|proof)\s*[:\-]",
                line.strip(),
                re.IGNORECASE,
            )
        )

    def _is_meta_line(line: str) -> bool:
        return bool(
            re.match(
                r"^(let's start|we'll create|we will create|the user might want|this is straightforward|here is a simple problem|here is a simple mathematical problem|here is a mathematical problem|let's create|i will create)\b",
                line.strip().lower(),
            )
        )

    def _strip_marker_noise(line: str) -> str:
        stripped = re.sub(r"^[\*\s]+|[\*\s]+$", "", line)
        stripped = re.sub(r"^(tutor|assistant|user|system)\s*:\s*", "", stripped, flags=re.IGNORECASE)
        return stripped.strip()

    problem_lines = []
    in_problem = False
    for line in lines:
        if _is_solution_marker(line):
            break
        if _is_problem_marker(line):
            in_problem = True
            line = _strip_marker_noise(line)
            parts = re.split(r"[:\-]", line, maxsplit=1)
            if len(parts) == 2:
                remainder = parts[1].strip()
                if remainder:
                    problem_lines.append(_strip_marker_noise(remainder))
            continue
        if in_problem:
            if _is_meta_line(line):
                continue
            problem_lines.append(_strip_marker_noise(line))
            continue

        label_match = re.match(
            r"^\*{0,2}\s*(here is the problem|here is the exercise|here is the task|try this|let's try this)\s*[:\-]?\s*(.*)$",
            line.strip(),
            re.IGNORECASE,
        )
        if label_match:
            in_problem = True
            remainder = _strip_marker_noise(label_match.group(2).strip())
            if remainder:
                problem_lines.append(remainder)

    if problem_lines:
        combined = " ".join(problem_lines).strip()
        combined = _strip_marker_noise(combined)
        if _looks_intro_only(combined) or _is_meta_task_generation_reply(combined) or not _has_concrete_math_payload(combined):
            return ""
        return combined

    def _is_intro_line(line: str) -> bool:
        return re.match(
            r"^(here is|here's|below is|sure|okay|ok|of course|certainly|let's|i can|i will|here you go)\b",
            line.strip().lower(),
        )

    def _looks_like_problem_line(line: str) -> bool:
        lowered = line.lower()
        if line.strip().endswith("?"):
            return True
        if re.search(r"\b(solve|find|compute|determine|evaluate|simplify|factor|expand|differentiate|integrate|prove|show)\b", lowered):
            return True
        if re.search(r"[0-9]", line) and re.search(r"[=\+\-*/\^]", line):
            return True
        if re.search(r"\b(x|y|z|n|k)\b", lowered) and re.search(r"[=\+\-*/\^]", line):
            return True
        if re.search(r"\b(probability|matrix|triangle|circle|function|limit|derivative|integral|log|ln)\b", lowered):
            return True
        return False

    def _is_solution_like_line(line: str) -> bool:
        lowered = line.lower()
        if re.match(r"^\s*\d+\s*[\.)]", lowered):
            return True
        if re.search(r"\bstep[-\s]*by[-\s]*step\b", lowered):
            return True
        if re.search(r"\b(let's solve|let us solve|we can solve|we will solve)\b", lowered):
            return True
        if re.search(r"\b(first,\s*subtract|now\s*subtract)\b", lowered):
            return True
        if re.search(r"\b(solution|answer|explanation|derivation|proof|step\s*\d+)\b", lowered):
            return True
        if re.search(r"\b(quadratic formula|discriminant|complete the square|we can|let's|now we|first,? we|next,? we|therefore|thus)\b", lowered):
            return True
        return False

    problem = ""
    next_index = 0
    for idx, line in enumerate(lines):
        if _is_solution_like_line(line):
            break
        if ":" in line:
            prefix, tail = line.split(":", 1)
            if _looks_like_problem_line(tail):
                prefix = prefix.strip()
                tail = tail.strip()
                if _looks_like_problem_line(prefix) and not _is_intro_line(prefix):
                    problem = f"{prefix}: {tail}".strip()
                else:
                    problem = tail
                next_index = idx + 1
                break
        if line.endswith(":") and idx + 1 < len(lines):
            next_line = lines[idx + 1]
            if not _is_solution_like_line(next_line) and _looks_like_problem_line(next_line):
                if _looks_like_problem_line(line) and not _is_intro_line(line):
                    problem = f"{line} {next_line}".strip()
                else:
                    problem = next_line
                next_index = idx + 2
                break
        if _is_meta_line(line):
            continue
        if _is_intro_line(line) and not _looks_like_problem_line(line):
            continue
        if _looks_like_problem_line(line):
            problem = line
            next_index = idx + 1
            break

    if not problem:
        problem = lines[0]
        next_index = 1

    if _is_meta_task_generation_reply(problem) or _looks_intro_only(problem) or not _has_concrete_math_payload(problem):
        return ""

    encouragement = ""
    for line in lines[next_index:]:
        if _is_solution_like_line(line):
            break
        if re.search(r"\b(try|attempt|give it a try|you can do it|good luck|have a go)\b", line, re.IGNORECASE):
            encouragement = re.split(r"(?<=[.!?])\s+", line)[0].strip()
            break

    if encouragement:
        return f"{problem} {encouragement}".strip()
    return problem


def _normalize_math_delimiters(text: str) -> str:
    if not text:
        return text
    normalized = text
    normalized = re.sub(r"\\\\\[(.+?)\\\\\]", r"$$\1$$", normalized, flags=re.DOTALL)
    normalized = re.sub(r"\\\[(.+?)\\\]", r"$$\1$$", normalized, flags=re.DOTALL)
    normalized = re.sub(r"\\\\\((.+?)\\\\\)", r"$\1$", normalized)
    normalized = re.sub(r"\\\((.+?)\\\)", r"$\1$", normalized)
    return normalized


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

        intent = _classify_intent(user_message, history_context)
        category_intent = "follow_up" if intent in {"answer_request", "answer_check"} else intent

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
        last_assistant = ""
        for message in history[-12:]:
            role = message.get("role", "user")
            content = message.get("content", "")
            history_lines.append(f"{role.upper()}: {content}")
            if role == "assistant":
                last_assistant = content

        current_problem = _extract_current_problem_by_intent(history, user_message, intent)
        problem_type = _detect_problem_type(current_problem)

        if _is_missing_problem_request(user_message) and last_assistant and not _contains_problem_statement(last_assistant):
            intent = "task_generation"
            category_intent = "task_generation"

        try:
            tokenizer = self.__class__._tokenizer
            model = self.__class__._model
            intent_instruction = _intent_instruction(intent)
            history_block = "\n".join(history_lines) if history_lines else "(no previous messages)"
            user_payload = (
                "Conversation so far:\n"
                f"{history_block}\n\n"
                "Current user message:\n"
                f"{user_message}\n\n"
                "Tutor instruction:\n"
                f"{intent_instruction}"
            )
            messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_payload},
            ]

            prompt_text = tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True,
            )
            inputs = tokenizer(prompt_text, return_tensors="pt")
            inputs = {key: value.to(model.device) for key, value in inputs.items()}

            with torch.no_grad():
                max_new_tokens = settings.qwen_max_new_tokens
                if intent == "task_generation":
                    max_new_tokens = min(max_new_tokens, 80)
                outputs = model.generate(
                    **inputs,
                    max_new_tokens=max_new_tokens,
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

        category = str(parsed.get("category", "")).strip()
        completed = bool(parsed.get("problem_completed", False))
        reply = str(parsed.get("reply", "")).strip()

        allowed_categories = {"task_generation", "problem_solving", "follow_up", "non_math"}
        if category not in allowed_categories:
            category = category_intent
        elif category != "non_math" and category != category_intent:
            category = category_intent

        if not _is_meaningful_text(reply):
            cleaned = _clean_raw_answer(raw, user_message, history_lines)
            if _is_meaningful_text(cleaned):
                reply = cleaned
                category = category_intent
                completed = _infer_completed(reply)
                logger.warning("USING_RAW_TEXT_REPLY")
            else:
                reply = "Let's continue step by step. What have you tried so far?"
                category = "problem_solving"
                completed = False

        if re.search(r"\b(conversation so far|current user message|tutor instruction)\b", reply, re.IGNORECASE) or re.search(
            r"\b(user|assistant|system)\s*:", reply, re.IGNORECASE
        ):
            reply = _strip_prompt_scaffolding(reply, user_message, history_lines)

        if intent == "task_generation":
            reply = _normalize_task_generation_text(reply)
            reply = _trim_task_generation_reply(reply)
            completed = False
            reply = _sanitize_task_reply(reply)
            reply = _ensure_task_problem(reply, user_message)
        elif intent in {"problem_solving", "follow_up"}:
            reply = _trim_to_single_step(reply)

        if intent == "follow_up" and last_assistant and _is_repeated_reply(reply, last_assistant):
            reply = _fallback_follow_up_hint(last_assistant, history_context, problem_type, current_problem)
            completed = False

        reply = _finalize_step_reply(
            intent,
            reply,
            last_assistant,
            history_context,
            problem_type,
            current_problem,
        )

        reply = _normalize_math_delimiters(reply).strip()

        if intent == "answer_request":
            reply = _answer_request_reply(problem_type, last_assistant, history_context, current_problem)
        if intent == "answer_check":
            reply = _answer_check_reply(problem_type, current_problem, user_message, last_assistant, history_context)

        if not _is_meaningful_text(reply) and category != "non_math":
            if intent == "task_generation":
                reply = _fallback_problem(user_message)
                completed = False
            else:
                reply = _next_step_hint(problem_type, last_assistant, history_context, current_problem)
                completed = False

        completed = _should_mark_completed(intent, user_message, reply)

        if category == "non_math":
            reply = MATH_SCOPE_REFUSAL
            completed = False

        return {
            "category": category,
            "problem_completed": completed,
            "reply": reply,
        }


tutor = QwenMathTutor()
