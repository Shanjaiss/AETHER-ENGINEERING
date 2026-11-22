from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class DynamicPlanStep(BaseModel):
    step_order: int
    title: str
    description: str
    target_files: List[str] = Field(default_factory=list)
    prerequisite_steps: List[int] = Field(default_factory=list)
    risk_level: str = "LOW"  # LOW | MEDIUM | HIGH | CRITICAL
    acceptance_criteria: List[str] = Field(default_factory=list)
    verification_strategy: str = "Automated unit test execution"
    status: str = "PENDING"  # PENDING | IN_PROGRESS | COMPLETED | FAILED | SKIPPED

class DynamicPlanOutput(BaseModel):
    objective: str
    existing_implementation_analysis: str
    required_files: List[str] = Field(default_factory=list)
    proposed_modifications: List[DynamicPlanStep] = Field(default_factory=list)
    dependencies: List[str] = Field(default_factory=list)
    acceptance_criteria: List[str] = Field(default_factory=list)
    verification_strategy: str
    risk_level: str = "LOW"
    expected_limitations: List[str] = Field(default_factory=list)
    revision_count: int = 0

class PlanValidationResult(BaseModel):
    is_valid: bool
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    ordered_steps: List[DynamicPlanStep] = Field(default_factory=list)

class ScopeCreepEvaluation(BaseModel):
    has_scope_creep: bool
    reasons: List[str] = Field(default_factory=list)
    requires_renewed_approval: bool

