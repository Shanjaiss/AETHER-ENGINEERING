from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class IntentType(str, Enum):
    INFORMATION_REQUEST = "INFORMATION_REQUEST"
    READONLY_ANALYSIS = "READONLY_ANALYSIS"
    CODE_MODIFICATION = "CODE_MODIFICATION"
    TEST_EXECUTION = "TEST_EXECUTION"
    HIGH_RISK_OPERATION = "HIGH_RISK_OPERATION"

class TaskCategory(str, Enum):
    BUG_FIX = "BUG_FIX"
    FEATURE_IMPLEMENTATION = "FEATURE_IMPLEMENTATION"
    REFACTORING = "REFACTORING"
    TEST_GENERATION = "TEST_GENERATION"
    DEPENDENCY_UPDATE = "DEPENDENCY_UPDATE"
    SECURITY_HARDENING = "SECURITY_HARDENING"
    DOCUMENTATION = "DOCUMENTATION"
    GENERAL_QUERY = "GENERAL_QUERY"

class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class AcceptanceCriterion(BaseModel):
    id: str
    description: str
    verification_type: str = "TEST"  # TEST | CODE_INSPECTION | MANUAL_VERIFICATION
    target_area: Optional[str] = None
    passed: bool = False

class AmbiguityAssessment(BaseModel):
    is_ambiguous: bool
    ambiguity_score: float = Field(ge=0.0, le=1.0, description="0.0 = completely clear, 1.0 = highly ambiguous")
    missing_elements: List[str] = Field(default_factory=list)
    clarification_questions: List[str] = Field(default_factory=list)

class TaskUnderstandingResult(BaseModel):
    task_id: Optional[str] = None
    intent: IntentType
    category: TaskCategory
    primary_technology: Optional[str] = None
    summary: str
    target_files_hinted: List[str] = Field(default_factory=list)
    detected_dependencies: List[str] = Field(default_factory=list)
    risk_level: RiskLevel
    risk_reasons: List[str] = Field(default_factory=list)
    requires_approval_gate: bool
    ambiguity: AmbiguityAssessment
    acceptance_criteria: List[AcceptanceCriterion] = Field(default_factory=list)
    created_at: Optional[str] = None

