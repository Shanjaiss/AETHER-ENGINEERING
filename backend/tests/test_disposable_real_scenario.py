import pytest
import shutil
from pathlib import Path
from backend.app.core.config import settings
from backend.app.services.llm.gateway import (
    BaseLLMAdapter,
    ImplementationPlanOutput,
    PlanStepOutput,
    CodingOutput,
    PatchFileOutput
)
from backend.app.services.orchestrator.planning_agent import PlanningAgent
from backend.app.services.coding_engine.coding_agent import CodingAgent
from backend.app.services.debugging.self_debugging_agent import SelfDebuggingAgent
from backend.app.services.review.review_engine import ReviewEngine

class DisposableAuditMockAdapter(BaseLLMAdapter):
    """Adapter for disposable FastAPI audit test."""

    def generate_plan(self, requirement, repo_summary, context_files):
        return ImplementationPlanOutput(
            summary="Repair discount calculation formula in main.py and verify regression tests",
            rationale="Current implementation subtracts raw percentage value instead of applying fractional reduction",
            steps=[
                PlanStepOutput(
                    step_order=1,
                    title="Fix calculate_discount Formula",
                    description="Update calculation to price * (1 - discount_percent / 100)",
                    target_files=["main.py"],
                    risk_level="LOW",
                    acceptance_criteria="Calculates accurate percentage discount"
                )
            ],
            predicted_file_changes=["main.py"],
            overall_risk="LOW"
        )

    def generate_patch(self, requirement, plan_step, context_files):
        # Step 1: Initial flawed patch to verify self-debugging catches it
        return CodingOutput(
            patches=[
                PatchFileOutput(
                    file_path="main.py",
                    action="modify",
                    diff_or_content="""def calculate_discount(price: float, discount_percent: float) -> float:
    # First attempt: still buggy
    return price - discount_percent
""",
                    explanation="First pass"
                )
            ],
            notes="Initial draft"
        )

    def diagnose_and_repair(self, requirement, failed_command, stdout, stderr, context_files):
        return CodingOutput(
            patches=[
                PatchFileOutput(
                    file_path="main.py",
                    action="modify",
                    diff_or_content="""def calculate_discount(price: float, discount_percent: float) -> float:
    return price * (1.0 - discount_percent / 100.0)
""",
                    explanation="Repaired discount formula to use fractional ratio"
                )
            ],
            notes="Diagnosed AssertionError and corrected percentage calculation"
        )

@pytest.fixture
def disposable_repo():
    disposable_dir = Path("/tmp/disposable_fastapi_audit_repo")
    if disposable_dir.exists():
        shutil.rmtree(disposable_dir)
    disposable_dir.mkdir(parents=True, exist_ok=True)

    # Ensure /tmp is allowed during this test
    if "/tmp" not in settings.ALLOWED_REPO_ROOTS:
        if isinstance(settings.ALLOWED_REPO_ROOTS, list):
            settings.ALLOWED_REPO_ROOTS.append("/tmp")

    main_py = disposable_dir / "main.py"
    initial_content = """def calculate_discount(price: float, discount_percent: float) -> float:
    return price - discount_percent
"""
    main_py.write_text(initial_content)

    test_py = disposable_dir / "test_main.py"
    test_py.write_text("""from main import calculate_discount

def test_discount():
    assert calculate_discount(100.0, 20.0) == 80.0
    assert calculate_discount(50.0, 20.0) == 40.0
""")

    (disposable_dir / "requirements.txt").write_text("fastapi>=0.110.0\npytest>=8.0.0\n")

    yield disposable_dir, initial_content

    # Cleanup disposable repo after test
    if disposable_dir.exists():
        shutil.rmtree(disposable_dir)

def test_unconfigured_model_blocks_execution(client, disposable_repo):
    """Step 3 requirement: If no real model provider is configured, classify AI test as BLOCKED."""
    repo_dir, _ = disposable_repo

    # Set provider to unconfigured
    orig_provider = settings.LLM_PROVIDER
    settings.LLM_PROVIDER = "unconfigured"

    try:
        ws_res = client.post("/api/v1/workspaces/", json={
            "name": "Disposable Unconfigured WS",
            "path": str(repo_dir)
        })
        assert ws_res.status_code == 201
        ws_id = ws_res.json()["id"]

        task_res = client.post("/api/v1/tasks/", json={
            "workspace_id": ws_id,
            "title": "Fix Discount Calculation",
            "description": "Analyze this FastAPI repository and fix calculation"
        })
        assert task_res.status_code == 201
        task_id = task_res.json()["id"]

        # Attempt plan generation
        plan_res = client.post(f"/api/v1/planning/{task_id}/generate")
        # MUST return 503 BLOCKED
        assert plan_res.status_code == 503
        assert "AI Model Gateway is unconfigured" in plan_res.json()["detail"]
    finally:
        settings.LLM_PROVIDER = orig_provider

def test_disposable_e2e_engineering_lifecycle(client, db_session, disposable_repo):
    """Step 3: Complete lifecycle execution on real disposable repository."""
    repo_dir, initial_content = disposable_repo

    # 1. Register workspace
    ws_res = client.post("/api/v1/workspaces/", json={
        "name": "Disposable Audit WS",
        "path": str(repo_dir)
    })
    assert ws_res.status_code == 201
    ws_id = ws_res.json()["id"]

    # 2. Scan repository
    scan_res = client.post("/api/v1/repositories/scan", json={
        "workspace_id": ws_id,
        "path": str(repo_dir)
    })
    assert scan_res.status_code == 200
    repo_summary = scan_res.json()
    assert "FastAPI" in repo_summary["frameworks"]

    # 3. Create engineering task
    task_res = client.post("/api/v1/tasks/", json={
        "workspace_id": ws_id,
        "title": "Fix Discount Formula Defect",
        "description": "Analyze this FastAPI repository, identify the defect, implement the correct solution, write or update regression tests, run permitted verification, and prepare a complete code review."
    })
    task_id = task_res.json()["id"]

    adapter = DisposableAuditMockAdapter()

    # 4. Generate plan
    planning_agent = PlanningAgent(db=db_session, adapter=adapter)
    task = planning_agent.generate_plan(task_id)
    assert task.status == "AWAITING_PLAN_APPROVAL"
    assert len(task.plan_steps) == 1
    assert task.plan_steps[0].target_files == ["main.py"]

    # 5. Developer Plan Approval Gate #1
    app_res = client.post(f"/api/v1/planning/{task_id}/approve", json={
        "decision": "APPROVED",
        "notes": "Plan approved for execution in isolated sandbox."
    })
    assert app_res.status_code == 200

    # 6. Execute in isolated sandbox
    coding_agent = CodingAgent(db=db_session, adapter=adapter)
    task = coding_agent.execute_coding(task_id)
    assert task.status == "VERIFYING"
    assert task.isolated_workspace_path is not None
    # 7. Crucial check: Original repo in /tmp is 100% untouched
    assert (repo_dir / "main.py").read_text() == initial_content

    # 8. Test Verification & Self-Debugging
    self_debug_agent = SelfDebuggingAgent(db=db_session, adapter=adapter)
    task = self_debug_agent.verify_and_repair(task_id)

    # 9. Test results & verification evidence
    assert task.status == "AWAITING_DIFF_APPROVAL"
    assert task.current_phase == "VERIFIED_ALL_TESTS_PASSED"
    assert task.repair_attempts == 1

    # 10. Code Review & Conflict check
    review_engine = ReviewEngine(db=db_session)
    report = review_engine.generate_quality_report(task_id)
    assert report.total_files_changed == 1
    assert report.static_analysis_passed is True
    assert report.test_evidence["final_status"] == "SUCCESS"

    conflicts = review_engine.detect_conflicts(task_id)
    assert conflicts.has_conflicts is False

    # 11. Developer Approval Gate #2
    dec_res = client.post(f"/api/v1/review/{task_id}/decision", json={
        "decision": "APPROVED",
        "notes": "Verified passing tests, approved for merge."
    })
    assert dec_res.status_code == 200

    # 12. Safe application to source repository
    apply_res = client.post(f"/api/v1/review/{task_id}/apply")
    assert apply_res.status_code == 200
    assert apply_res.json()["status"] == "COMPLETED"

    # 13. Original repository is now updated with verified passing code
    final_content = (repo_dir / "main.py").read_text()
    assert "price * (1.0 - discount_percent / 100.0)" in final_content

