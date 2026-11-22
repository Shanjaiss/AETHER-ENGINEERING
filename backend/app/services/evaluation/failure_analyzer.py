"""
AETHER ENGINEER - Intelligent Failure Analysis Engine
Module 8: Automated failure categorization, empirical evidence extraction,
root-cause analysis, and recommended remediations.
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel

from backend.app.schemas.benchmark import (
    BenchmarkTaskResult,
    FailureCategory,
    EvaluationOutcome
)

class StructuredFailureDiagnosis(BaseModel):
    task_id: str
    task_name: str
    outcome: EvaluationOutcome
    failure_category: FailureCategory
    expected_behavior: str
    observed_behavior: str
    confirmed_evidence: str
    suspected_hypothesis: str
    recommended_remediation: str

class FailureAnalyzer:
    """Analyzes benchmark results and produces structured failure diagnoses."""

    @staticmethod
    def diagnose_result(result: BenchmarkTaskResult) -> StructuredFailureDiagnosis:
        evidence = result.verification_evidence or "No stdout/stderr captured."
        reason = result.failure_reason or "Unknown failure"

        # Separate confirmed empirical facts from hypotheses
        confirmed = f"Outcome: {result.outcome.value}. Exit Code != 0. Details: {reason}"
        hypothesis = "AI model generated logic that diverged from acceptance test expectations."
        remediation = "Inspect acceptance criteria and refine AST symbol retrieval context."

        if result.failure_category == FailureCategory.SANDBOX_RESTRICTION or result.security_violations > 0:
            confirmed = f"Security Policy Block: {result.security_violations} boundary violation(s) detected."
            hypothesis = "Generated patch attempted to modify paths outside allowed workspace roots."
            remediation = "Enforce canonical path resolution before applying file modifications."
        elif result.failure_category == FailureCategory.REGRESSION_DEFECT:
            confirmed = "Pre-existing baseline tests failed after patch was applied."
            hypothesis = "Patch altered shared helper function signature breaking dependents."
            remediation = "Run blast-radius dependency check and include dependent callers in test pass."
        elif result.failure_category == FailureCategory.INVALID_PATCH_FORMAT:
            confirmed = "PatchEngine could not parse diff or identify target file."
            hypothesis = "Model output truncated or failed to follow exact PatchFileOutput JSON schema."
            remediation = "Enforce structured output schema validation with fallback repair prompt."
        elif result.failure_category == FailureCategory.TIMEOUT:
            confirmed = f"Execution exceeded resource limit: {result.duration_seconds}s."
            hypothesis = "Code modification introduced infinite loop or blocking I/O operation."
            remediation = "Instrument TestRunner with per-process timeout enforcement."

        return StructuredFailureDiagnosis(
            task_id=result.task_id,
            task_name=result.name,
            outcome=result.outcome,
            failure_category=result.failure_category,
            expected_behavior="Code modification passes all independent acceptance tests with zero regressions.",
            observed_behavior=f"Task ended with outcome {result.outcome.value}.",
            confirmed_evidence=confirmed,
            suspected_hypothesis=hypothesis,
            recommended_remediation=remediation
        )

    @classmethod
    def generate_suite_diagnosis(cls, results: List[BenchmarkTaskResult]) -> List[StructuredFailureDiagnosis]:
        failed_tasks = [r for r in results if r.outcome != EvaluationOutcome.RESOLVED]
        return [cls.diagnose_result(r) for r in failed_tasks]

