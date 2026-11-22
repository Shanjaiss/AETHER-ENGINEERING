import pytest
from backend.app.services.task_understanding.task_analyzer import TaskUnderstandingEngine
from backend.app.schemas.task_understanding import IntentType, TaskCategory, RiskLevel

def test_bug_fix_classification():
    result = TaskUnderstandingEngine.analyze(
        title="Fix JWT token expiry in auth.py",
        description="Tokens that are expired should return False from authenticate() instead of True.",
        repo_files=["auth.py", "test_auth.py"]
    )
    assert result.intent == IntentType.CODE_MODIFICATION
    assert result.category == TaskCategory.BUG_FIX
    assert "auth.py" in result.target_files_hinted
    assert result.risk_level == RiskLevel.HIGH  # Affects auth
    assert result.requires_approval_gate is True
    assert len(result.acceptance_criteria) >= 2
    assert result.ambiguity.is_ambiguous is False

def test_feature_implementation_classification():
    result = TaskUnderstandingEngine.analyze(
        title="Add system status endpoint",
        description="Implement GET /status returning JSON with status healthy and version string.",
        repo_files=["app.py", "test_app.py"]
    )
    assert result.intent == IntentType.CODE_MODIFICATION
    assert result.category == TaskCategory.FEATURE_IMPLEMENTATION
    assert result.risk_level == RiskLevel.MEDIUM
    assert result.requires_approval_gate is True
    assert result.ambiguity.is_ambiguous is False

def test_information_request():
    result = TaskUnderstandingEngine.analyze(
        title="Explain database migration architecture",
        description="How does Alembic run migrations and where is Base defined?"
    )
    assert result.intent == IntentType.INFORMATION_REQUEST
    assert result.risk_level == RiskLevel.LOW
    assert result.requires_approval_gate is False

def test_readonly_analysis():
    result = TaskUnderstandingEngine.analyze(
        title="Analyze repository dependencies",
        description="Inspect all package manifests and check for deprecated libraries."
    )
    assert result.intent == IntentType.READONLY_ANALYSIS
    assert result.risk_level == RiskLevel.LOW
    assert result.requires_approval_gate is False

def test_high_risk_operation():
    result = TaskUnderstandingEngine.analyze(
        title="Drop table tasks and purge schema",
        description="Execute drop table and rm -rf old migrations."
    )
    assert result.intent == IntentType.HIGH_RISK_OPERATION
    assert result.risk_level == RiskLevel.CRITICAL
    assert result.requires_approval_gate is True
    assert any("destructive" in r.lower() for r in result.risk_reasons)

def test_ambiguity_detection_vague_input():
    result = TaskUnderstandingEngine.analyze(
        title="Fix it",
        description="make it work please"
    )
    assert result.ambiguity.is_ambiguous is True
    assert result.ambiguity.ambiguity_score >= 0.4
    assert len(result.ambiguity.missing_elements) > 0
    assert len(result.ambiguity.clarification_questions) > 0

def test_ambiguity_detection_clear_input():
    result = TaskUnderstandingEngine.analyze(
        title="Refactor calculate_total in billing.py",
        description="Extract tax calculation into a separate helper function format_tax() and ensure test_billing.py passes.",
        repo_files=["billing.py", "test_billing.py"]
    )
    assert result.ambiguity.is_ambiguous is False
    assert result.ambiguity.ambiguity_score < 0.4
    assert result.category == TaskCategory.REFACTORING

