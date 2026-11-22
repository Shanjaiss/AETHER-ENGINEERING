import pytest
from pathlib import Path
from backend.app.core.config import settings
from backend.app.services.llm.gateway import (
    BaseLLMAdapter,
    CodingOutput,
    PatchFileOutput
)
from backend.app.services.coding_engine.workspace_isolator import WorkspaceIsolator
from backend.app.services.debugging.self_debugging_agent import SelfDebuggingAgent
from backend.app.services.debugging.failure_classifier import FailureClassifier

class SelfDebuggingMockAdapter(BaseLLMAdapter):
    """Adapter that supplies the correct fix during self-debugging."""

    def generate_plan(self, requirement, repo_summary, context_files):
        raise NotImplementedError()

    def generate_patch(self, requirement, plan_step, context_files):
        raise NotImplementedError()

    def diagnose_and_repair(self, requirement, failed_command, stdout, stderr, context_files):
        # Return correct math implementation
        return CodingOutput(
            patches=[
                PatchFileOutput(
                    file_path="calc.py",
                    action="modify",
                    diff_or_content="def add(a, b):\n    return a + b\n",
                    explanation="Fixed off-by-one error"
                )
            ],
            notes="Repaired addition formula"
        )

class UnfixableMockAdapter(BaseLLMAdapter):
    """Adapter that returns an ineffective patch to test bounded retry limits."""

    def generate_plan(self, requirement, repo_summary, context_files):
        raise NotImplementedError()

    def generate_patch(self, requirement, plan_step, context_files):
        raise NotImplementedError()

    def diagnose_and_repair(self, requirement, failed_command, stdout, stderr, context_files):
        return CodingOutput(
            patches=[
                PatchFileOutput(
                    file_path="calc.py",
                    action="modify",
                    diff_or_content="def add(a, b):\n    return a + b - 1\n",
                    explanation="Still broken"
                )
            ],
            notes="Still failing"
        )

@pytest.fixture
def seeded_bug_repo():
    repo_dir = settings.resolved_workspace_root / "seeded_bug_repo"
    repo_dir.mkdir(parents=True, exist_ok=True)

    # Seeded bug: add returns 3 instead of 4
    calc_file = repo_dir / "calc.py"
    calc_file.write_text("def add(a, b):\n    return a + b - 1\n")

    test_file = repo_dir / "test_calc.py"
    test_file.write_text("from calc import add\n\ndef test_add():\n    assert add(2, 2) == 4\n")

    return repo_dir

def test_failure_classification():
    pytest_err = "def test_add():\n> assert add(2, 2) == 4\nE AssertionError: assert 3 == 4"
    diag = FailureClassifier.classify(pytest_err, "", 1)
    assert diag["category"] == "ASSERTION_ERROR"
    assert "test_add" in diag["summary"]

def test_self_debugging_repairs_seeded_bug(client, db_session, seeded_bug_repo):
    # 1. Register workspace
    ws_res = client.post("/api/v1/workspaces/", json={
        "name": "Seeded Bug WS",
        "path": str(seeded_bug_repo)
    })
    ws_id = ws_res.json()["id"]

    # 2. Create task
    task_res = client.post("/api/v1/tasks/", json={
        "workspace_id": ws_id,
        "title": "Repair math bug",
        "description": "Fix bug in calc.py so test_calc passes"
    })
    task_id = task_res.json()["id"]

    # 3. Create isolated workspace
    isolator = WorkspaceIsolator()
    isolated_path = isolator.create_isolated_copy(task_id, seeded_bug_repo)

    from backend.app.models.task import Task
    task = db_session.query(Task).filter(Task.id == task_id).first()
    task.isolated_workspace_path = str(isolated_path)
    db_session.commit()

    # 4. Run Self-Debugging Agent
    agent = SelfDebuggingAgent(db=db_session, adapter=SelfDebuggingMockAdapter())
    result_task = agent.verify_and_repair(task_id)

    # 5. Verify Successful repair
    assert result_task.status == "AWAITING_DIFF_APPROVAL"
    assert result_task.current_phase == "VERIFIED_ALL_TESTS_PASSED"
    assert result_task.repair_attempts == 1

    # Verify execution history
    exec_res = client.get(f"/api/v1/verification/{task_id}/executions")
    assert exec_res.status_code == 200
    executions = exec_res.json()
    assert len(executions) == 2
    assert executions[0]["status"] == "FAILURE"
    assert executions[1]["status"] == "SUCCESS"

    # Verify original file untouched
    orig_calc = seeded_bug_repo / "calc.py"
    assert "return a + b - 1" in orig_calc.read_text()

def test_bounded_repair_loop_halts_at_max(client, db_session, seeded_bug_repo):
    # Register and create task
    ws_res = client.post("/api/v1/workspaces/", json={
        "name": "Bounded Loop WS",
        "path": str(seeded_bug_repo)
    })
    ws_id = ws_res.json()["id"]

    task_res = client.post("/api/v1/tasks/", json={
        "workspace_id": ws_id,
        "title": "Unfixable task",
        "description": "Attempt repair on unfixable issue"
    })
    task_id = task_res.json()["id"]

    isolator = WorkspaceIsolator()
    isolated_path = isolator.create_isolated_copy(task_id, seeded_bug_repo)

    from backend.app.models.task import Task
    task = db_session.query(Task).filter(Task.id == task_id).first()
    task.isolated_workspace_path = str(isolated_path)
    db_session.commit()

    # Run with adapter that never fixes the bug
    agent = SelfDebuggingAgent(db=db_session, adapter=UnfixableMockAdapter())
    failed_task = agent.verify_and_repair(task_id)

    assert failed_task.status == "FAILED"
    assert failed_task.current_phase == "MAX_REPAIR_ATTEMPTS_EXCEEDED"
    assert failed_task.repair_attempts == settings.MAX_REPAIR_ATTEMPTS

