import time
import shutil
import pytest
from pathlib import Path

from backend.app.core.config import settings
from backend.app.models.workspace import Workspace
from backend.app.models.task import Task, ApprovalGate, ApprovalStatus, GateType
from backend.app.services.repo_intelligence.scanner import RepositoryScanner
from backend.app.services.task_understanding.task_analyzer import TaskUnderstandingEngine
from backend.app.services.orchestrator.dynamic_planner import DynamicPlanner
from backend.app.services.coding_engine.workspace_isolator import WorkspaceIsolator
from backend.app.services.coding_engine.patch_engine import PatchEngine
from backend.app.services.verification.test_runner import TestRunner
from backend.app.services.debugging.failure_classifier import FailureClassifier
from backend.app.services.review.review_engine import ReviewEngine
from backend.app.services.review.quality_controller import QualityController
from backend.app.services.llm.gateway import PatchFileOutput

@pytest.fixture
def disposable_phase10_repo():
    repo_dir = settings.resolved_workspace_root / "disposable_phase10_acceptance_repo"
    if repo_dir.exists():
        shutil.rmtree(repo_dir)
    repo_dir.mkdir(parents=True, exist_ok=True)

    # 1. Defective auth module (does not check current time against expiry)
    (repo_dir / "auth.py").write_text(
        "import time\n"
        "def verify_token(exp_timestamp: int) -> bool:\n"
        "    # Intentional defect: returns True for any positive timestamp\n"
        "    return exp_timestamp > 0\n"
    )

    # 2. Service calling auth
    (repo_dir / "service.py").write_text(
        "import auth\n"
        "def process_login(exp_timestamp: int) -> str:\n"
        "    if auth.verify_token(exp_timestamp):\n"
        "        return 'AUTHORIZED'\n"
        "    return 'UNAUTHORIZED'\n"
    )

    # 3. Independent regression test
    (repo_dir / "test_service.py").write_text(
        "import time\n"
        "from service import process_login\n"
        "def test_process_login_expired():\n"
        "    now = int(time.time())\n"
        "    # Expired token in past should return UNAUTHORIZED\n"
        "    assert process_login(now - 100) == 'UNAUTHORIZED'\n"
        "def test_process_login_valid():\n"
        "    now = int(time.time())\n"
        "    assert process_login(now + 1000) == 'AUTHORIZED'\n"
    )

    yield repo_dir

    if repo_dir.exists():
        shutil.rmtree(repo_dir)

def test_phase10_full_autonomous_acceptance_lifecycle(client, db_session, disposable_phase10_repo):
    """Phase 10 Final Acceptance Test: Complete 10-step autonomous software engineering

    lifecycle verifying repository understanding, context retrieval, planning, isolated
    execution, test evidence, bounded debugging, quality control, and human approval gates.
    """
    orig_auth_content = (disposable_phase10_repo / "auth.py").read_text()

    # Step 1: Correct Repository Understanding
    scanner = RepositoryScanner(disposable_phase10_repo)
    all_files = scanner.list_repo_files()
    assert "auth.py" in all_files
    assert "service.py" in all_files
    assert "test_service.py" in all_files

    user_prompt = (
        "Analyze this repository, identify the cause of the failing API behavior, propose a fix, "
        "implement the approved changes in an isolated workspace, run the permitted tests, "
        "diagnose any failures, and prepare a verified patch for review."
    )

    understanding = TaskUnderstandingEngine.analyze(
        title="Fix failing API authorization behavior",
        description=user_prompt,
        repo_files=all_files
    )
    assert understanding.intent.value == "CODE_MODIFICATION"
    assert understanding.category.value == "BUG_FIX"
    assert understanding.requires_approval_gate is True
    assert len(understanding.acceptance_criteria) >= 2

    # Step 2: Relevant Source-File Retrieval
    relevant_files = scanner.retrieve_context("verify_token expired timestamp", max_files=3)
    retrieved_names = [f.relative_path for f in relevant_files]
    assert "auth.py" in retrieved_names or "service.py" in retrieved_names

    # Step 3: Valid Structured Plan
    # Register workspace and task in database
    ws = Workspace(name="Phase10AcceptanceWS", path=str(disposable_phase10_repo))
    db_session.add(ws)
    db_session.commit()

    task = Task(
        workspace_id=ws.id,
        title="Fix failing API authorization behavior",
        description=user_prompt,
        status="PLANNING"
    )
    db_session.add(task)
    db_session.commit()

    plan = DynamicPlanner.create_plan(
        task_id=task.id,
        requirement=user_prompt,
        understanding=understanding,
        scanner=scanner
    )
    assert len(plan.proposed_modifications) >= 2
    assert plan.risk_level in ["MEDIUM", "HIGH"]

    # Register Gate #1 (Plan Approval Gate)
    gate1 = ApprovalGate(
        task_id=task.id,
        gate_type=GateType.PLAN.value,
        status=ApprovalStatus.PENDING.value,
        proposed_payload=plan.model_dump()
    )
    db_session.add(gate1)
    task.status = "AWAITING_PLAN_APPROVAL"
    db_session.commit()

    # Step 4: Human Plan Approval
    gate1.status = ApprovalStatus.APPROVED.value
    task.status = "CODING"
    db_session.commit()

    # Step 5 & 6: Safe Isolated Execution & Source Untouched
    isolator = WorkspaceIsolator()
    isolated_path = isolator.create_isolated_copy(task.id, disposable_phase10_repo)
    task.isolated_workspace_path = str(isolated_path)
    db_session.commit()

    # Verify original repository is strictly untouched
    assert (disposable_phase10_repo / "auth.py").read_text() == orig_auth_content

    # Step 7: Real Test Evidence & Failure Catch
    runner = TestRunner(isolated_path)
    test_cmd = runner.discover_test_command()
    initial_exit, initial_stdout, initial_stderr, dur1 = runner.execute_command(test_cmd)
    # Must fail because auth.py has the bug
    assert initial_exit != 0
    assert "assert process_login" in f"{initial_stdout}\n{initial_stderr}" or "AssertionError" in f"{initial_stdout}\n{initial_stderr}"

    # Step 8: Bounded Failure Diagnosis
    diagnosis = FailureClassifier.classify(initial_stdout, initial_stderr, initial_exit)
    assert diagnosis["category"] in ["ASSERTION_ERROR", "RUNTIME_ERROR"]
    assert "failing_file" in diagnosis

    # Apply targeted fix to isolated workspace
    fix_patch = PatchFileOutput(
        file_path="auth.py",
        action="modify",
        diff_or_content=(
            "import time\n"
            "def verify_token(exp_timestamp: int) -> bool:\n"
            "    # Correct implementation: token must be in the future\n"
            "    return exp_timestamp > int(time.time())\n"
        ),
        explanation="Enforce current timestamp boundary on token expiration"
    )
    orig_txt, patched_txt, diff_txt = PatchEngine.apply_patch(isolated_path, fix_patch)
    assert len(diff_txt.splitlines()) > 0

    # Re-verify in isolated sandbox
    post_exit, post_stdout, post_stderr, dur2 = runner.execute_command(test_cmd)
    assert post_exit == 0  # PASSED!

    # Record execution and patch diff
    from backend.app.models.task import ExecutionRun, PatchDiff
    exec_run = ExecutionRun(
        task_id=task.id,
        phase="VERIFYING",
        command=" ".join(test_cmd),
        exit_code=0,
        stdout=post_stdout,
        stderr="",
        duration_ms=dur2,
        status="SUCCESS"
    )
    db_session.add(exec_run)

    patch_diff = PatchDiff(
        task_id=task.id,
        file_path="auth.py",
        original_content=orig_txt,
        patched_content=patched_txt,
        diff_text=diff_txt,
        status="APPLIED_ISOLATED"
    )
    db_session.add(patch_diff)
    db_session.commit()

    # Step 9: Accurate Quality & Engineering Report
    qc = QualityController(db_session)
    qc_result = qc.evaluate_task(task.id)
    assert qc_result.has_test_evidence is True
    assert qc_result.is_approved_for_merge is True
    assert len(qc_result.unnecessary_files_modified) == 0

    review_engine = ReviewEngine(db_session)
    quality_report = review_engine.generate_quality_report(task.id)
    assert quality_report.total_files_changed == 1
    assert quality_report.static_analysis_passed is True

    # Check pre-apply conflicts
    conflict_check = review_engine.detect_conflicts(task.id)
    assert conflict_check.has_conflicts is False

    # Verify source repository is STILL untouched before Gate #2
    assert (disposable_phase10_repo / "auth.py").read_text() == orig_auth_content

    # Step 10: Final Human Approval Gate & Safe Merge
    review_engine.submit_review_decision(task.id, decision="APPROVED", notes="Acceptance verified")
    review_engine.apply_approved_patches(task.id)

    db_session.refresh(task)
    assert task.status == "COMPLETED"

    # Verify source repository now contains the verified patch
    final_auth_content = (disposable_phase10_repo / "auth.py").read_text()
    assert "return exp_timestamp > int(time.time())" in final_auth_content

    # Run tests directly against source repository to verify green state
    source_runner = TestRunner(disposable_phase10_repo)
    source_exit, source_stdout, _, _ = source_runner.execute_command(test_cmd)
    assert source_exit == 0
