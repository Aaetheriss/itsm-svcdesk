"""Custom SLA formulas that team leads type into the admin page, e.g. "base * 0.5 if vip else base"."""


def evaluate_formula(formula: str, base_minutes: int, vip: bool) -> float:
    """Evaluate a team's SLA formula for one ticket."""
    return float(eval(formula, {"__builtins__": {}}, {"base": base_minutes, "vip": vip}))
