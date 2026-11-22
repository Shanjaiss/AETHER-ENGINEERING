import time
from typing import Dict, Any, List, Optional, Tuple
from pydantic import BaseModel, Field

from backend.app.core.config import settings
from backend.app.core.logging import logger

class ModelCapabilities(BaseModel):
    provider: str
    model_name: str
    is_configured: bool
    context_window_tokens: int
    supports_json_schema: bool
    cost_per_1k_input_usd: float
    cost_per_1k_output_usd: float
    max_concurrency: int = 1

class TokenUsage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    estimated_cost_usd: float

MODEL_SPECS: Dict[str, Dict[str, Any]] = {
    "gpt-4o-mini": {
        "provider": "openai",
        "context_window": 128000,
        "json_mode": True,
        "input_cost_1k": 0.00015,
        "output_cost_1k": 0.00060,
    },
    "gpt-4o": {
        "provider": "openai",
        "context_window": 128000,
        "json_mode": True,
        "input_cost_1k": 0.00500,
        "output_cost_1k": 0.01500,
    },
    "claude-3-5-sonnet-20241022": {
        "provider": "anthropic",
        "context_window": 200000,
        "json_mode": True,
        "input_cost_1k": 0.00300,
        "output_cost_1k": 0.01500,
    },
    "gemini-2.5-flash": {
        "provider": "gemini",
        "context_window": 1000000,
        "json_mode": True,
        "input_cost_1k": 0.000075,
        "output_cost_1k": 0.00030,
    },
    "llama3": {
        "provider": "ollama",
        "context_window": 8192,
        "json_mode": True,
        "input_cost_1k": 0.0,
        "output_cost_1k": 0.0,
    }
}

class ModelManager:
    """Manages multi-provider capabilities, token budgeting, cost estimation,

    and concurrency guards for Mac M1 8 GB memory constraint.
    """

    @classmethod
    def get_capabilities(cls, model_name: Optional[str] = None) -> ModelCapabilities:
        model = model_name or settings.LLM_MODEL
        spec = MODEL_SPECS.get(model, {
            "provider": settings.LLM_PROVIDER,
            "context_window": 16000,
            "json_mode": True,
            "input_cost_1k": 0.001,
            "output_cost_1k": 0.002
        })

        provider = spec.get("provider", settings.LLM_PROVIDER).lower()
        is_configured = False
        if provider == "openai" and settings.OPENAI_API_KEY:
            is_configured = True
        elif provider == "anthropic" and settings.ANTHROPIC_API_KEY:
            is_configured = True
        elif provider == "gemini" and settings.GEMINI_API_KEY:
            is_configured = True
        elif provider == "ollama" and settings.OLLAMA_BASE_URL:
            is_configured = True

        return ModelCapabilities(
            provider=provider,
            model_name=model,
            is_configured=is_configured,
            context_window_tokens=spec.get("context_window", 16000),
            supports_json_schema=spec.get("json_mode", True),
            cost_per_1k_input_usd=spec.get("input_cost_1k", 0.0),
            cost_per_1k_output_usd=spec.get("output_cost_1k", 0.0),
            max_concurrency=1  # Apple Silicon M1 8GB keeps concurrency strictly bounded
        )

    @classmethod
    def estimate_tokens(cls, text: str) -> int:
        """Rough token approximation: 1 token ~= 4 characters."""
        return max(1, len(text) // 4)

    @classmethod
    def calculate_cost(cls, prompt_tokens: int, completion_tokens: int, model_name: Optional[str] = None) -> TokenUsage:
        caps = cls.get_capabilities(model_name)
        cost_in = (prompt_tokens / 1000.0) * caps.cost_per_1k_input_usd
        cost_out = (completion_tokens / 1000.0) * caps.cost_per_1k_output_usd
        total_cost = round(cost_in + cost_out, 6)

        return TokenUsage(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
            estimated_cost_usd=total_cost
        )

    @classmethod
    def budget_context(cls, text: str, max_tokens: int = 6000) -> Tuple[str, int]:
        """Truncates text to fit within max_tokens budget if needed."""
        tokens = cls.estimate_tokens(text)
        if tokens <= max_tokens:
            return text, tokens

        char_limit = max_tokens * 4
        truncated = text[:char_limit] + "\n...[Context truncated to adhere to token budget]..."
        return truncated, max_tokens

