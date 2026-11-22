import datetime
from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class EvaluationOutcome(str, Enum):
    RESOLVED = "RESOLVED"
    UNRESOLVED = "UNRESOLVED"
    PARTIAL = "PARTIAL"
    TIMEOUT = "TIMEOUT"
    INFRASTRUCTURE_BLOCKED = "INFRASTRUCTURE_BLOCKED"
    MODEL_ERROR = "MODEL_ERROR"
    POLICY_VIOLATION = "POLICY_VIOLATION"

class FailureCategory(str, Enum):
    NONE = "NONE"
    INCORRECT_REPO_UNDERSTANDING = "INCORRECT_REPO_UNDERSTANDING"
    MISSING_CONTEXT = "MISSING_CONTEXT"
    INVALID_PLANNING = "INVALID_PLANNING"
    INCORRECT_CODE = "INCORRECT_CODE"
    INVALID_PATCH_FORMAT = "INVALID_PATCH_FORMAT"
    DEPENDENCY_ERROR = "DEPENDENCY_ERROR"
    MODEL_ERROR = "MODEL_ERROR"
    TEST_FAILURE = "TEST_FAILURE"
    RESOURCE_EXHAUSTION = "RESOURCE_EXHAUSTION"
    TIMEOUT = "TIMEOUT"
    SANDBOX_RESTRICTION = "SANDBOX_RESTRICTION"
    UNSUPPORTED_ENV = "UNSUPPORTED_ENV"
    REGRESSION_DEFECT = "REGRESSION_DEFECT"

class BenchmarkDefinition(BaseModel):
    id: str
    name: str
    category: str
    description: str
    expected_files: List[str]
    language: Optional[str] = "python"
    difficulty: Optional[str] = "MEDIUM"
    subcategory: Optional[str] = ""
    is_held_out: Optional[bool] = False

class BenchmarkTaskDefinition(BaseModel):
    id: str
    name: str
    language: str = "python"
    difficulty: str = "MEDIUM"  # EASY, MEDIUM, HARD
    category: str
    subcategory: str
    description: str
    initial_files: Dict[str, str]
    test_files: Dict[str, str] = Field(
        default_factory=dict,
        description="Independent evaluator acceptance tests. Hidden from agent context."
    )
    baseline_passing_tests: Optional[Dict[str, str]] = Field(
        default_factory=dict,
        description="Pre-existing baseline tests that must remain passing (regression check)."
    )
    expected_files: List[str]
    reference_fix: Optional[Dict[str, str]] = None
    permitted_operations: List[str] = Field(
        default_factory=lambda: ["read", "write", "test_execute"]
    )
    resource_limits: Dict[str, Any] = Field(
        default_factory=lambda: {"timeout_seconds": 30, "max_memory_mb": 150}
    )
    is_held_out: bool = False

class BenchmarkRunItem(BaseModel):
    id: str
    benchmark_id: str
    name: str
    category: str
    model_name: str
    test_passed: bool
    duration_seconds: float
    repair_attempts: int
    unnecessary_file_changes: int = 0
    security_violations: int = 0
    outcome: EvaluationOutcome = EvaluationOutcome.RESOLVED
    failure_category: FailureCategory = FailureCategory.NONE
    created_at: datetime.datetime

class BenchmarkTaskResult(BaseModel):
    task_id: str
    name: str
    category: str
    subcategory: str
    language: str
    difficulty: str
    model_name: str
    outcome: EvaluationOutcome
    test_passed: bool
    patch_applied: bool
    build_passed: bool
    original_tests_passed: bool
    acceptance_tests_passed: bool
    unrelated_files_modified: int = 0
    security_violations: int = 0
    repair_attempts: int = 0
    first_attempt_resolved: bool = False
    duration_seconds: float = 0.0
    model_latency_seconds: float = 0.0
    tool_latency_seconds: float = 0.0
    model_calls: int = 0
    tool_calls: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    estimated_cost_usd: float = 0.0
    failure_category: FailureCategory = FailureCategory.NONE
    failure_reason: Optional[str] = None
    verification_evidence: Optional[str] = None
    diff_summary: Optional[str] = None

class BenchmarkSummaryReport(BaseModel):
    suite_id: str = "custom-se-50"
    version: str = "1.0.0"
    timestamp: str = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())
    model_name: str
    environment: str = "Apple Silicon M1 (8GB)"
    total_tasks: int = 0
    attempted_tasks: int = 0
    resolved_tasks: int = 0
    unresolved_tasks: int = 0
    blocked_tasks: int = 0
    resolution_rate_percent: float = 0.0
    first_attempt_rate_percent: float = 0.0
    repair_success_rate_percent: float = 0.0
    patch_apply_rate_percent: float = 0.0
    avg_duration_seconds: float = 0.0
    median_duration_seconds: float = 0.0
    avg_model_latency_seconds: float = 0.0
    total_model_calls: int = 0
    total_tool_calls: int = 0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_cost_usd: float = 0.0
    total_security_violations: int = 0
    # Legacy fields for Phase 8/9 backwards compatibility
    total_benchmarks_run: int = 0
    verified_pass_rate_percent: float = 0.0
    task_completion_rate_percent: float = 0.0
    avg_repair_attempts: float = 0.0
    category_breakdown: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    category_metrics: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    failure_breakdown: Dict[str, int] = Field(default_factory=dict)
    task_results: List[BenchmarkTaskResult] = Field(default_factory=list)
    runs: List[BenchmarkRunItem] = Field(default_factory=list)

class AblationStudyResult(BaseModel):
    config_id: str
    config_name: str
    description: str
    tasks_attempted: int
    tasks_resolved: int
    resolution_rate_percent: float
    retrieval_accuracy_percent: float
    regression_rate_percent: float
    avg_duration_seconds: float
    total_tokens: int
    estimated_cost_usd: float

class AblationStudyReport(BaseModel):
    timestamp: str
    benchmark_suite: str
    model_name: str
    configurations: List[AblationStudyResult]
    key_findings: List[str]

class ModelComparisonEntry(BaseModel):
    model_identifier: str
    provider: str
    resolved_tasks: int
    total_tasks: int
    resolution_rate_percent: float
    avg_duration_seconds: float
    avg_model_latency_seconds: float
    total_cost_usd: float
    security_violations: int

class ModelComparisonReport(BaseModel):
    timestamp: str
    suite_id: str
    models: List[ModelComparisonEntry]
    summary_verdict: str

class SecurityTestFixture(BaseModel):
    id: str
    name: str
    attack_vector: str
    description: str
    payload_or_command: str
    expected_defense: str
    prevented: bool = False
    evidence: str = ""

class SecurityBenchmarkReport(BaseModel):
    timestamp: str
    total_fixtures: int
    prevented_count: int
    breached_count: int
    prevention_rate_percent: float
    all_prevented: bool
    fixtures: List[SecurityTestFixture]
