import pytest
from backend.app.models.task import Task, PatchDiff, ExecutionRun, PlanStep
from backend.app.models.workspace import Workspace
from backend.app.services.review.quality_controller import QualityController

def test_quality_controller_requires_real_test_evidence(db_session, tmp_path):
    ws = Workspace(name="QC_WS", path=str(tmp_path))
    db_session.add(ws)
    db_session.commit()

    task = Task(workspace_id=ws.id, title="QC Task", description="Testing quality control", status="VERIFYING")
    db_session.add(task)
    db_session.commit()

    # Step targeting auth.py
    step = PlanStep(task_id=task.id, step_order=1, title="S1", description="", target_files=["auth.py"])
    db_session.add(step)

    # Patch targeting auth.py
    patch = PatchDiff(task_id=task.id, file_path="auth.py", diff_text="+auth", status="APPLIED")
    db_session.add(patch)
    db_session.commit()

    qc = QualityController(db_session)

    # Case 1: No execution runs -> Fails test evidence
    res1 = qc.evaluate_task(task.id)
    assert res1.has_test_evidence is False
    assert res1.is_approved_for_merge is False

    # Case 2: Execution run with failure (exit code 1) -> retry justified
    failed_run = ExecutionRun(task_id=task.id, phase="VERIFYING", command="pytest", exit_code=1, stdout="", stderr="failed", duration_ms=100, status="FAILURE")
    db_session.add(failed_run)
    db_session.commit()

    res2 = qc.evaluate_task(task.id)
    assert res2.has_test_evidence is False
    assert res2.retry_justified is True
    assert res2.is_approved_for_merge is False

    # Case 3: Extraneous unapproved file modified
    bad_patch = PatchDiff(task_id=task.id, file_path="rogue_unapproved.py", diff_text="+bad", status="APPLIED")
    db_session.add(bad_patch)
    db_session.commit()

    res3 = qc.evaluate_task(task.id)
    assert "rogue_unapproved.py" in res3.unnecessary_files_modified
    assert res3.is_approved_for_merge is False

    # Case 4: Passing execution run & clean patches -> Ready for merge
    db_session.delete(bad_patch)
    success_run = ExecutionRun(task_id=task.id, phase="VERIFYING", command="pytest", exit_code=0, stdout="passed", stderr="", duration_ms=50, status="SUCCESS")
    db_session.add(success_run)
    db_session.commit()

    res4 = qc.evaluate_task(task.id)
    assert res4.has_test_evidence is True
    assert len(res4.unnecessary_files_modified) == 0
    assert res4.is_approved_for_merge is True
    assert "Quality verification PASSED" in res4.reflection_notes
