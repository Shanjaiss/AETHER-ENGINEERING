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
from backend.app.services.coding_engine.coding_agent import CodingAgent
from backend.app.services.coding_engine.patch_engine import PatchEngine
from backend.app.core.security import SecurityException

class CodingMockLLMAdapter(BaseLLMAdapter):
    """Deterministic coding mock adapter."""

    def generate_plan(self, requirement, repo_summary, context_files):
        return ImplementationPlanOutput(
            summary="Test plan",
            rationale="Test rationale",
            steps=[
                PlanStepOutput(
                    step_order=1,
                    title="Update auth.py",
                    description="Fix expiry bug",
                    target_files=["auth.py"],
                    risk_level="LOW",
                    acceptance_criteria="Pass"
                )
            ],
            predicted_file_changes=["auth.py"],
            overall_risk="LOW"
        )

    def generate_patch(self, requirement, plan_step, context_files):
        return CodingOutput(
            patches=[
                PatchFileOutput(
                    file_path="auth.py",
                    action="modify",
                    diff_or_content="def authenticate_user():\n    # Patched: check token expiration\n    return True\n",
                    explanation="Added token expiration verification"
                )
            ],
            notes="Patch generated successfully"
        )

    def diagnose_and_repair(self, requirement, failed_command, stdout, stderr, context_files):
        return CodingOutput(patches=[], notes="")

@pytest.fixture
def original_repo():
    repo_dir = settings.resolved_workspace_root / "original_test_repo"
    repo_dir.mkdir(parents=True, exist_ok=True)
    auth_file = repo_dir / "auth.py"
    initial_content = "def authenticate_user():\n    return False\n"
    auth_file.write_text(initial_content)
    return repo_dir, initial_content

def test_autonomous_coding_in_isolated_workspace(client, db_session, original_repo):
    repo_dir, original_content = original_repo

    # 1. Register workspace
    ws_res = client.post("/api/v1/workspaces/", json={
        "name": "Original WS",
        "path": str(repo_dir)
    })
    ws_id = ws_res.json()["id"]

    # 2. Create task and add plan step
    task_res = client.post("/api/v1/tasks/", json={
        "workspace_id": ws_id,
        "title": "Fix Auth Bug",
        "description": "Fix bug in auth.py"
    })
    task_id = task_res.json()["id"]

    # Add plan step
    from backend.app.models.task import PlanStep
    step = PlanStep(
        task_id=task_id,
        step_order=1,
        title="Patch auth.py",
        description="Fix authentication",
        target_files=["auth.py"],
        risk_level="LOW",
        status="APPROVED"
    )
    db_session.add(step)
    db_session.commit()

    # 3. Execute Coding Agent
    agent = CodingAgent(db=db_session, adapter=CodingMockLLMAdapter())
    updated_task = agent.execute_coding(task_id)

    assert updated_task.status == "VERIFYING"
    assert updated_task.isolated_workspace_path is not None
    isolated_path = Path(updated_task.isolated_workspace_path)
    assert isolated_path.exists()
    assert isolated_path != repo_dir

    # 4. Verify patch applied to isolated copy
    isolated_auth = isolated_path / "auth.py"
    assert isolated_auth.exists()
    assert "Patched: check token expiration" in isolated_auth.read_text()

    # 5. CRITICAL ACCEPTANCE CHECK: Original repo is 100% UNCHANGED
    original_auth = repo_dir / "auth.py"
    assert original_auth.read_text() == original_content
    assert "Patched" not in original_auth.read_text()

    # 6. Verify PatchDiff recorded
    diffs = client.get(f"/api/v1/coding/{task_id}/diffs").json()
    assert len(diffs) == 1
    assert diffs[0]["file_path"] == "auth.py"
    assert "--- a/auth.py" in diffs[0]["diff_text"]
    assert "+    # Patched: check token expiration" in diffs[0]["diff_text"]

    # 7. Test Rollback
    agent.rollback(task_id)
    assert isolated_auth.read_text() == original_content

def test_patch_engine_boundary_and_security(tmp_path):
    sandbox = tmp_path / "sandbox"
    sandbox.mkdir()
    (sandbox / "safe.py").write_text("print('hello')\n")

    # Path traversal attack in patch target
    malicious_patch = PatchFileOutput(
        file_path="../../outside.py",
        action="modify",
        diff_or_content="malicious",
        explanation="attack"
    )
    is_valid, reason = PatchEngine.validate_patch(sandbox, malicious_patch)
    assert is_valid is False
    assert "Directory traversal" in reason

    with pytest.raises(SecurityException):
        PatchEngine.apply_patch(sandbox, malicious_patch)

    # Sensitive file target
    secret_patch = PatchFileOutput(
        file_path=".env",
        action="modify",
        diff_or_content="EXPOSED_KEY=xyz",
        explanation="forbidden"
    )
    is_valid_sec, reason_sec = PatchEngine.validate_patch(sandbox, secret_patch)
    assert is_valid_sec is False
    assert "forbidden" in reason_sec

