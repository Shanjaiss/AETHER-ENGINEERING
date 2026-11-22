import pytest
from pathlib import Path
from backend.app.core.config import settings
from backend.app.core.security import SecurityException
from backend.app.models.workspace import Workspace
from backend.app.models.task import Task, ApprovalGate, ApprovalStatus, GateType
from backend.app.services.orchestrator.specialized_agents import SpecializedAgentOrchestrator
from backend.app.services.orchestrator.task_memory import TaskMemoryManager

@pytest.fixture
def agent_workspace(db_session):
    ws_path = settings.resolved_workspace_root / "specialized_agent_ws"
    ws_path.mkdir(parents=True, exist_ok=True)
    (ws_path / "calc.py").write_text("def add(a, b): return a + b\n")
    (ws_path / "test_calc.py").write_text("from calc import add\ndef test_add(): assert add(1, 2) == 3\n")

    ws = Workspace(name="SpecializedAgentWS", path=str(ws_path))
    db_session.add(ws)
    db_session.commit()
    db_session.refresh(ws)
    return ws

def test_coding_agent_privilege_enforcement(db_session, agent_workspace):
    task = Task(
        workspace_id=agent_workspace.id,
        title="Unapproved Coding Attempt",
        description="Try coding before plan approval",
        status="PLANNING"
    )
    db_session.add(task)
    db_session.commit()

    orchestrator = SpecializedAgentOrchestrator(db_session)

    # Calling coding without Gate #1 approval MUST raise SecurityException
    with pytest.raises(SecurityException) as exc_info:
        orchestrator.run_coding(task.id)
    assert "Privileged operation denied" in str(exc_info.value.detail)

def test_full_role_orchestration_cycle(db_session, agent_workspace):
    task = Task(
        workspace_id=agent_workspace.id,
        title="Fix calc addition",
        description="Verify and update addition helper in calc.py",
        status="PENDING"
    )
    db_session.add(task)
    db_session.commit()

    orchestrator = SpecializedAgentOrchestrator(db_session)

    # 1. Role: Repo Analysis
    analysis = orchestrator.run_repo_analysis(task.id)
    assert "summary" in analysis
    assert analysis["summary"]["file_count"] >= 2

    # 2. Role: Planning
    plan = orchestrator.run_planning(task.id)
    assert len(plan.proposed_modifications) >= 2
    db_session.refresh(task)
    assert task.status == "AWAITING_PLAN_APPROVAL"

    # 3. Approve Gate #1
    gate = db_session.query(ApprovalGate).filter(
        ApprovalGate.task_id == task.id,
        ApprovalGate.gate_type == GateType.PLAN.value
    ).first()
    assert gate is not None
    gate.status = ApprovalStatus.APPROVED.value
    db_session.commit()

    # 4. Role: Coding (now permitted)
    diffs = orchestrator.run_coding(task.id)
    db_session.refresh(task)
    assert task.status == "CODING"
    assert task.isolated_workspace_path is not None
    assert Path(task.isolated_workspace_path).exists()

    # 5. Role: Testing
    exec_run = orchestrator.run_testing(task.id)
    assert exec_run.exit_code == 0
    assert exec_run.status == "SUCCESS"

    # 6. Role: Code Review
    review_data = orchestrator.run_code_review(task.id)
    assert "quality_report" in review_data
    db_session.refresh(task)
    assert task.status == "AWAITING_DIFF_APPROVAL"

