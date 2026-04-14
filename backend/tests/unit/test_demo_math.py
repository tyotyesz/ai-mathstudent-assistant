from app.core.demo_math import solve_question


def test_quadratic_solution():
    answer, steps = solve_question("x^2 -5x +6 = 0")
    assert "Roots" in answer
    assert len(steps) >= 2


def test_arithmetic_solution():
    answer, steps = solve_question("(2+3)*4")
    assert answer == "20"
    assert steps[-1].startswith("Result = 20")


def test_fallback_message():
    answer, steps = solve_question("integrate sin x")
    assert "demo mode" in answer.lower()
    assert len(steps) >= 1
