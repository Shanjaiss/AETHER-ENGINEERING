import pytest
from backend.app.schemas.planning import DynamicPlanStep, DynamicPlanOutput
from backend.app.services.orchestrator.dynamic_planner import DynamicPlanner

def test_topological_sort_step_ordering():
    steps = [
        DynamicPlanStep(step_order=1, title="Step 1", description="", prerequisite_steps=[2]),
        DynamicPlanStep(step_order=2, title="Step 2", description="", prerequisite_steps=[]),
        DynamicPlanStep(step_order=3, title="Step 3", description="", prerequisite_steps=[1]),
    ]
    res = DynamicPlanner.validate_and_order_steps(steps)
    assert res.is_valid is True
    ordered_titles = [s.title for s in res.ordered_steps]
    # Step 2 must come first, then Step 1, then Step 3
    assert ordered_titles == ["Step 2", "Step 1", "Step 3"]
    assert res.ordered_steps[0].step_order == 1
    assert res.ordered_steps[1].step_order == 2
    assert res.ordered_steps[2].step_order == 3

def test_cycle_detection_in_plan_steps():
    steps = [
        DynamicPlanStep(step_order=1, title="Step 1", description="", prerequisite_steps=[2]),
        DynamicPlanStep(step_order=2, title="Step 2", description="", prerequisite_steps=[1]),
    ]
    res = DynamicPlanner.validate_and_order_steps(steps)
    assert res.is_valid is False
    assert any("Circular dependency" in err for err in res.errors)

def test_scope_creep_detection():
    orig_plan = DynamicPlanOutput(
        objective="Fix auth",
        existing_implementation_analysis="ok",
        required_files=["auth.py"],
        proposed_modifications=[
            DynamicPlanStep(step_order=1, title="S1", description="", target_files=["auth.py"])
        ],
        dependencies=[],
        acceptance_criteria=[],
        verification_strategy="test",
        risk_level="MEDIUM",
        expected_limitations=[]
    )

    # 1. Scope creep via new files
    creep_plan_files = orig_plan.model_copy(deep=True)
    creep_plan_files.required_files = ["auth.py", "unapproved_admin.py"]
    eval_files = DynamicPlanner.detect_scope_creep(orig_plan, creep_plan_files)
    assert eval_files.has_scope_creep is True
    assert eval_files.requires_renewed_approval is True
    assert any("unapproved_admin.py" in r for r in eval_files.reasons)

    # 2. Scope creep via step explosion (> 30%)
    creep_plan_steps = orig_plan.model_copy(deep=True)
    creep_plan_steps.proposed_modifications = [
        DynamicPlanStep(step_order=1, title="S1", description="", target_files=["auth.py"]),
        DynamicPlanStep(step_order=2, title="S2", description="", target_files=["auth.py"]),
        DynamicPlanStep(step_order=3, title="S3", description="", target_files=["auth.py"]),
    ]
    eval_steps = DynamicPlanner.detect_scope_creep(orig_plan, creep_plan_steps)
    assert eval_steps.has_scope_creep is True
    assert eval_steps.requires_renewed_approval is True

    # 3. Scope creep via elevated risk level
    creep_plan_risk = orig_plan.model_copy(deep=True)
    creep_plan_risk.risk_level = "CRITICAL"
    eval_risk = DynamicPlanner.detect_scope_creep(orig_plan, creep_plan_risk)
    assert eval_risk.has_scope_creep is True
    assert any("elevated" in r for r in eval_risk.reasons)

