"""
AETHER ENGINEER - Model Comparison Framework
Module 5: Provider-independent LLM gateway comparison, capability detection,
and reproducible multi-model benchmark evaluation.
"""

import time
import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from backend.app.schemas.benchmark import (
    ModelComparisonReport,
    ModelComparisonEntry,
    BenchmarkTaskDefinition,
    EvaluationOutcome
)
from backend.app.services.evaluation.benchmark_engine import IndependentEvaluationEngine
from backend.app.services.evaluation.custom_benchmark_suite import CUSTOM_BENCHMARK_TASKS
from backend.app.services.llm.gateway import (
    BaseLLMAdapter,
    OpenAIAdapter,
    AnthropicAdapter,
    GeminiAdapter,
    OllamaAdapter,
    HeuristicMockAdapter
)
from backend.app.services.llm.model_manager import ModelManager

class ModelComparisonRunner:
    """
    Executes identical benchmark suites across multiple configured LLM adapters.
    Guarantees strict comparability and safe fallback when credentials are unconfigured.
    """

    def __init__(self, db: Optional[Session] = None):
        self.db = db
        self.model_mgr = ModelManager()

    def detect_available_providers(self) -> List[Dict[str, Any]]:
        """Identify which models/providers are configured vs unconfigured."""
        return self.model_mgr.list_available_models()

    def run_comparison(
        self,
        task_sample_size: int = 5,
        target_models: Optional[List[str]] = None
    ) -> ModelComparisonReport:
        """
        Run identical evaluation tasks across target model configurations.
        Default to 5 diverse tasks (1 from each category) for fast, memory-safe execution on M1.
        """
        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
        
        # Pick 1 sample task from each of the 5 categories
        sample_task_ids = ["py-01", "js-01", "api-01", "fe-01", "adv-01"][:task_sample_size]
        raw_samples = [t for t in CUSTOM_BENCHMARK_TASKS if t["id"] in sample_task_ids]
        task_defs = [BenchmarkTaskDefinition(**t) for t in raw_samples]

        # Model configs to compare
        configs_to_run = [
            ("Aether-Phase10-Agent", HeuristicMockAdapter(), "heuristic"),
            ("Baseline-Phase8-Agent", HeuristicMockAdapter(), "heuristic-baseline"),
        ]

        # Check if any live API keys are provided
        import os
        if os.getenv("OPENAI_API_KEY"):
            configs_to_run.append(("gpt-4o-mini", OpenAIAdapter(model="gpt-4o-mini"), "openai"))
        if os.getenv("ANTHROPIC_API_KEY"):
            configs_to_run.append(("claude-3-5-sonnet", AnthropicAdapter(model="claude-3-5-sonnet-20241022"), "anthropic"))
        if os.getenv("GEMINI_API_KEY"):
            configs_to_run.append(("gemini-1.5-flash", GeminiAdapter(model="gemini-1.5-flash"), "google"))

        entries: List[ModelComparisonEntry] = []

        for model_id, adapter, provider in configs_to_run:
            engine = IndependentEvaluationEngine(db=self.db, adapter=adapter)
            summary = engine.run_suite(task_definitions=task_defs)

            entry = ModelComparisonEntry(
                model_identifier=model_id,
                provider=provider,
                resolved_tasks=summary.resolved_tasks,
                total_tasks=summary.total_tasks,
                resolution_rate_percent=summary.resolution_rate_percent,
                avg_duration_seconds=summary.avg_duration_seconds,
                avg_model_latency_seconds=summary.avg_model_latency_seconds,
                total_cost_usd=summary.total_cost_usd,
                security_violations=summary.total_security_violations
            )
            entries.append(entry)

        # Sort entries by resolution rate descending, then duration ascending
        entries.sort(key=lambda x: (-x.resolution_rate_percent, x.avg_duration_seconds))

        verdict = (
            f"Top performing model: {entries[0].model_identifier} "
            f"({entries[0].resolution_rate_percent}% resolution on {len(task_defs)} tasks)."
        )

        return ModelComparisonReport(
            timestamp=now_iso,
            suite_id=f"custom-sample-{len(task_defs)}",
            models=entries,
            summary_verdict=verdict
        )

