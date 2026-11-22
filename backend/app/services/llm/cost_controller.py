from typing import Dict, Any, Optional

# Standard blended pricing per 1M tokens (input / output)
MODEL_PRICING = {
    "gemini-1.5-pro": {"input_per_m": 1.25, "output_per_m": 5.00},
    "gemini-1.5-flash": {"input_per_m": 0.075, "output_per_m": 0.30},
    "gpt-4o": {"input_per_m": 2.50, "output_per_m": 10.00},
    "gpt-4o-mini": {"input_per_m": 0.15, "output_per_m": 0.60},
    "claude-3-5-sonnet": {"input_per_m": 3.00, "output_per_m": 15.00},
    "claude-3-5-haiku": {"input_per_m": 0.80, "output_per_m": 4.00},
    "ollama": {"input_per_m": 0.0, "output_per_m": 0.0},
    "mock": {"input_per_m": 0.0, "output_per_m": 0.0}
}

class CostController:
    """Manages token accounting, cost calculations, inference budgets, and spending limits."""
    DEFAULT_PER_TASK_BUDGET_DOLLARS = 1.00
    DEFAULT_PER_TASK_TOKEN_BUDGET = 50000

    @classmethod
    def calculate_cost(cls, model_name: str, input_tokens: int, output_tokens: int) -> float:
        model_key = model_name.lower().strip()
        matched_pricing = None
        for k, v in MODEL_PRICING.items():
            if k in model_key:
                matched_pricing = v
                break
        if not matched_pricing:
            matched_pricing = MODEL_PRICING["gemini-1.5-flash"]

        cost = (input_tokens / 1_000_000.0) * matched_pricing["input_per_m"] + \
               (output_tokens / 1_000_000.0) * matched_pricing["output_per_m"]
        return round(cost, 6)

    @classmethod
    def check_task_budget(cls, current_cost: float, current_tokens: int, max_budget_dollars: float = DEFAULT_PER_TASK_BUDGET_DOLLARS) -> bool:
        """Returns True if within budget, False if budget exceeded."""
        if current_cost > max_budget_dollars:
            return False
        if current_tokens > cls.DEFAULT_PER_TASK_TOKEN_BUDGET:
            return False
        return True

