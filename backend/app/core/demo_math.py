import ast
import operator
import re
import time
from typing import List, Tuple

from .config import get_settings

settings = get_settings()


class SafeEvaluator(ast.NodeVisitor):
    ALLOWED_OPERATORS = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.Pow: operator.pow,
        ast.USub: operator.neg,
    }

    def visit(self, node):  # type: ignore[override]
        if isinstance(node, ast.Expression):
            return self.visit(node.body)
        if isinstance(node, ast.Num):
            return node.n
        if isinstance(node, ast.BinOp):
            op_type = type(node.op)
            if op_type not in self.ALLOWED_OPERATORS:
                raise ValueError("Operator not allowed")
            left = self.visit(node.left)
            right = self.visit(node.right)
            return self.ALLOWED_OPERATORS[op_type](left, right)
        if isinstance(node, ast.UnaryOp):
            op_type = type(node.op)
            if op_type not in self.ALLOWED_OPERATORS:
                raise ValueError("Unary operator not allowed")
            operand = self.visit(node.operand)
            return self.ALLOWED_OPERATORS[op_type](operand)
        if isinstance(node, ast.Constant):
            return node.value
        raise ValueError("Unsupported expression")


def artificial_delay() -> None:
    if settings.artificial_latency_ms > 0:
        time.sleep(settings.artificial_latency_ms / 1000.0)


def solve_quadratic(question: str) -> Tuple[str, List[str]]:
    pattern = r"([+-]?\d*\.?\d*)x\^2\s*([+-]\s*\d*\.?\d*)x\s*([+-]\s*\d*\.?\d*)\s*=\s*0"
    match = re.search(pattern, question.replace(" ", ""))
    if not match:
        return "", []
    a_raw, b_raw, c_raw = match.groups()
    a = float(a_raw) if a_raw not in ("", "+", "-") else (1.0 if a_raw != "-" else -1.0)
    b = float(b_raw.replace(" ", ""))
    c = float(c_raw.replace(" ", ""))
    discriminant = b ** 2 - 4 * a * c
    if discriminant < 0:
        return "No real roots", [f"Discriminant {discriminant} < 0"]
    sqrt_d = discriminant ** 0.5
    x1 = (-b + sqrt_d) / (2 * a)
    x2 = (-b - sqrt_d) / (2 * a)
    steps = [
        f"Compute discriminant D = b^2 - 4ac = {discriminant}",
        f"sqrt(D) = {sqrt_d}",
        f"Roots = (-b ± sqrt(D)) / (2a) = {x1}, {x2}",
    ]
    answer = f"Roots: {x1} and {x2}" if x1 != x2 else f"Double root: {x1}"
    return answer, steps


def solve_arithmetic(question: str) -> Tuple[str, List[str]]:
    try:
        expr = ast.parse(question, mode="eval")
        result = SafeEvaluator().visit(expr)
        steps = ["Parse expression", "Evaluate safely", f"Result = {result}"]
        return str(result), steps
    except Exception as exc:  # noqa: BLE001
        raise ValueError(f"Unsupported arithmetic expression: {exc}")


def solve_question(question: str) -> Tuple[str, List[str]]:
    artificial_delay()
    quadratic_answer, quadratic_steps = solve_quadratic(question)
    if quadratic_answer:
        return quadratic_answer, quadratic_steps
    try:
        arithmetic_answer, arithmetic_steps = solve_arithmetic(question)
        return arithmetic_answer, arithmetic_steps
    except ValueError:
        return (
            "I can only help with basic arithmetic and quadratics in demo mode.",
            [
                "Try a quadratic like x^2 - 5x + 6 = 0",
                "Or an arithmetic expression like (2+3)*4",
            ],
        )
