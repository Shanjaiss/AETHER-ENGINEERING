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
from backend.app.core.database import get_db

class TestMockLLMAdapter(BaseLLMAdapter):
    """Deterministic mock adapter used for test verifications without network costs."""

    def generate_plan(self, requirement, repo_summary, context_files):
        return ImplementationPlanOutput(
            summary="Refactor auth and repair token expiry",
            rationale="Identified missing expiry check in auth.py",
            steps=[
                PlanStepOutput(
                    step_order=1,
                    title="Add JWT Expiration Check",
                    description="Implement timestamp verification in authenticate_user",
                    target_files=["auth.py"],
                    risk_level="MEDIUM",
                    acceptance_criteria="Token expires after 3600 seconds"
                ),
                PlanStepOutput(
                    step_order=2,
                    title="Add Regression Test",
                    description="Create test_auth_expiry in tests/",
                    target_files=["tests/test_auth.py"],
                    risk_level="LOW",
                    acceptance_criteria="pytest passes"
                )
            ],
            predicted_file_changes=["auth.py", "tests/test_auth.py"],
            overall_risk="MEDIUM"
        )

    def generate_patch(self, requirement, plan_step, context_files):
        return CodingOutput(
            patches=[
                PatchFileOutput(
                    file_path="auth.py",
                    action="modify",
                    diff_or_content="@@ -3,3 +3,6 @@\n+    if is_expired(token):\n+        return False",
                    explanation="Added token expiry check"
                )
            ],
            notes="Patch created safely"
        )

    def diagnose_and_repair(self, requirement, failed_command, stdout, stderr, context_files):
        return CodingOutput(
            patches=[],
            notes="No repair needed"
        )

@pytest.fixture
def setup_task(client):
    ws_dir = settings.resolved_workspace_root / "planning_test_ws"
    ws_dir.mkdir(parents=True, exist_ok=True)
    (ws_dir / "auth.py").write_text("def authenticate_user(): pass\n")

    ws_res = client.post("/api/v1/workspaces/", json={
        "name": "Planning Test WS",
        "path": str(ws_dir)
    })
    ws_id = ws_res.json()["id"]

    task_res = client.post("/api/v1/tasks/", json={
        "workspace_id": ws_id,
        "title": "Fix token expiration bug",
        "description": "Inspect auth.py and fix token expiration handling"
    })
    return task_res.json()["id"]

def test_unconfigured_llm_returns_clear_error(client, setup_task):
    task_id = setup_task
    # Attempt plan generation with unconfigured default
    res = client.post(f"/api/v1/planning/{task_id}/generate")
    assert res.status_code == 503
    assert "AI Model Gateway is unconfigured" in res.json()["detail"]

    # Verify task state is marked FAILED with clear error summary
    task_check = client.get(f"/api/v1/tasks/{task_id}")
    assert task_check.json()["status"] == "FAILED"
    assert "AI Model Gateway is unconfigured" in task_check.json()["error_summary"]

def test_plan_generation_and_human_approval(client, db_session, setup_task):
    task_id = setup_task
    agent = PlanningAgent(db=db_session, adapter=TestMockLLMAdapter())

    # 1. Generate plan using mock adapter
    task = agent.generate_plan(task_id=task_id)
    assert task.status == "AWAITING_PLAN_APPROVAL"
    assert len(task.plan_steps) == 2
    assert task.plan_steps[0].title == "Add JWT Expiration Check"
    assert task.plan_steps[0].target_files == ["auth.py"]
    assert len(task.approvals) == 1
    assert task.approvals[0].status == "PENDING"

    # 2. Human Approval Gate
    approve_res = client.post(f"/api/v1/planning/{task_id}/approve", json={
        "decision": "APPROVED",
        "notes": "Plan looks sound, proceed to isolated sandbox coding."
    })
    assert approve_res.status_code == 200
    updated_task = approve_res.json()
    assert updated_task["status"] == "CODING"
    assert updated_task["current_phase"] == "PLAN_APPROVED_READY_FOR_CODING"

def test_plan_rejection(client, db_session, setup_task):
    task_id = setup_task
    agent = PlanningAgent(db=db_session, adapter=TestMockLLMAdapter())

    agent.generate_plan(task_id=task_id)

    # Reject plan
    reject_res = client.post(f"/api/v1/planning/{task_id}/approve", json={
        "decision": "REJECTED",
        "notes": "Unacceptable risk profile."
    })
    assert reject_res.status_code == 200
    assert reject_res.json()["status"] == "CANCELLED"

