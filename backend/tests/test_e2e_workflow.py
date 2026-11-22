import pytest
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

class E2EFullWorkflowMockAdapter(BaseLLMAdapter):
    """Adapter simulating the complete end-to-end intelligent engineering loop."""

    def generate_plan(self, requirement, repo_summary, context_files):
        return ImplementationPlanOutput(
            summary="Repair FastAPI JWT authentication expiry defect and add regression tests",
            rationale="Analysis revealed missing expiration checks in auth.py",
            steps=[
                PlanStepOutput(
                    step_order=1,
                    title="Implement JWT Expiration Validation",
                    description="Update authenticate() in auth.py to check token timestamp validity",
                    target_files=["auth.py"],
                    risk_level="MEDIUM",
                    acceptance_criteria="Expired tokens return False"
                ),
                PlanStepOutput(
                    step_order=2,
                    title="Add Regression Test Suite",
                    description="Implement test_auth.py to verify active and expired token handling",
                    target_files=["test_auth.py"],
                    risk_level="LOW",
                    acceptance_criteria="All pytest assertions pass"
                )
            ],
            predicted_file_changes=["auth.py", "test_auth.py"],
            overall_risk="MEDIUM"
        )

    def generate_patch(self, requirement, plan_step, context_files):
        # Step 1: initial buggy attempt (missing timestamp comparison) to trigger self-debugging
        if plan_step.get("order") == 1:
            return CodingOutput(
                patches=[
                    PatchFileOutput(
                        file_path="auth.py",
                        action="modify",
                        diff_or_content="""import time

def authenticate(token_exp: int) -> bool:
    # Initial draft: intentionally flawed logic to test verification engine
    return False
""",
                        explanation="Drafted auth handler"
                    )
                ],
                notes="Step 1 patch created"
            )
        else:
            return CodingOutput(
                patches=[
                    PatchFileOutput(
                        file_path="test_auth.py",
                        action="create",
                        diff_or_content="""import time
from auth import authenticate

def test_active_token():
    now = int(time.time())
    assert authenticate(now + 3600) is True

def test_expired_token():
    now = int(time.time())
    assert authenticate(now - 3600) is False
""",
                        explanation="Created regression tests"
                    )
                ],
                notes="Step 2 tests created"
            )

    def diagnose_and_repair(self, requirement, failed_command, stdout, stderr, context_files):
        # Self-debugging diagnosis returns verified fix
        return CodingOutput(
            patches=[
                PatchFileOutput(
                    file_path="auth.py",
                    action="modify",
                    diff_or_content="""import time

def authenticate(token_exp: int) -> bool:
    return token_exp > int(time.time())
""",
                    explanation="Repaired timestamp comparison"
                )
            ],
            notes="Diagnosed AssertionError and repaired timestamp verification"
        )

def test_full_acceptance_scenario(client, db_session):
    """
    Simulates Section 10 FINAL ACCEPTANCE SCENARIO:
    1. Inspects repository.
    2. Locates relevant source files.
    3. Analyzes issue.
    4. Creates implementation plan.
    5. Requests approval.
    6. Makes changes in isolated workspace.
    7. Runs permitted tests (catches seeded bug).
    8. Diagnoses failures.
    9. Attempts bounded repairs.
    10. Generates code diff.
    11. Produces test evidence.
    12. Displays engineering review.
    13. Requests final approval.
    14. Applies approved change safely to original repository.
    """
    # Setup sample FastAPI repository
    import shutil
    repo_dir = settings.resolved_workspace_root / "fastapi_app_e2e"
    if repo_dir.exists():
        shutil.rmtree(repo_dir)
    repo_dir.mkdir(parents=True, exist_ok=True)
    initial_auth = "def authenticate(token_exp: int) -> bool:\n    return True\n"
    (repo_dir / "auth.py").write_text(initial_auth)
    (repo_dir / "requirements.txt").write_text("fastapi>=0.110.0\npytest>=8.0.0\n")

    # Step 1: User registers workspace
    ws_res = client.post("/api/v1/workspaces/", json={
        "name": "FastAPI Auth Project",
        "path": str(repo_dir)
    })
    assert ws_res.status_code == 201
    ws_id = ws_res.json()["id"]

    # Step 2: User scans repository
    scan_res = client.post("/api/v1/repositories/scan", json={
        "workspace_id": ws_id,
        "path": str(repo_dir)
    })
    assert scan_res.status_code == 200
    assert "FastAPI" in scan_res.json()["frameworks"]

    # Step 3: User submits requirement
    user_requirement = "Inspect this FastAPI application, identify the authentication bug, implement a reliable fix, add regression tests, and show the complete changes."
    task_res = client.post("/api/v1/tasks/", json={
        "workspace_id": ws_id,
        "title": "Fix Authentication Bug",
        "description": user_requirement
    })
    assert task_res.status_code == 201
    task_id = task_res.json()["id"]

    adapter = E2EFullWorkflowMockAdapter()

    # Step 4: AI Planning Agent generates structured plan
    planning_agent = PlanningAgent(db=db_session, adapter=adapter)
    planned_task = planning_agent.generate_plan(task_id)
    assert planned_task.status == "AWAITING_PLAN_APPROVAL"
    assert len(planned_task.plan_steps) == 2

    # Step 5: Developer reviews and approves plan
    app_res = client.post(f"/api/v1/planning/{task_id}/approve", json={
        "decision": "APPROVED",
        "notes": "Plan approved for execution in isolated workspace."
    })
    assert app_res.status_code == 200
    assert app_res.json()["status"] == "CODING"

    # Step 6: Autonomous Coding Engine executes changes in isolated copy
    coding_agent = CodingAgent(db=db_session, adapter=adapter)
    coded_task = coding_agent.execute_coding(task_id)
    assert coded_task.status == "VERIFYING"
    assert coded_task.isolated_workspace_path is not None
    # Original repository remains strictly unchanged
    assert (repo_dir / "auth.py").read_text() == initial_auth

    # Step 7-9: Test Verification & Self-Debugging Loop
    self_debug_agent = SelfDebuggingAgent(db=db_session, adapter=adapter)
    verified_task = self_debug_agent.verify_and_repair(task_id)
    assert verified_task.status == "AWAITING_DIFF_APPROVAL"
    assert verified_task.current_phase == "VERIFIED_ALL_TESTS_PASSED"
    assert verified_task.repair_attempts == 1

    # Step 10-12: Developer Review Engine
    review_engine = ReviewEngine(db=db_session)
    report = review_engine.generate_quality_report(task_id)
    assert report.total_files_changed == 2
    assert report.static_analysis_passed is True
    assert report.test_evidence["final_status"] == "SUCCESS"

    conflicts = review_engine.detect_conflicts(task_id)
    assert conflicts.has_conflicts is False

    # Step 13: Developer submits final diff approval
    dec_res = client.post(f"/api/v1/review/{task_id}/decision", json={
        "decision": "APPROVED",
        "notes": "All tests verified passing. Approved for merge to source."
    })
    assert dec_res.status_code == 200

    # Step 14: Safe application to original repository
    final_res = client.post(f"/api/v1/review/{task_id}/apply")
    assert final_res.status_code == 200
    assert final_res.json()["status"] == "COMPLETED"

    # Final verification on original repository files:
    merged_auth = (repo_dir / "auth.py").read_text()
    assert "token_exp > int(time.time())" in merged_auth
    assert (repo_dir / "test_auth.py").exists()
