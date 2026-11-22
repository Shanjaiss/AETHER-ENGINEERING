import pytest
from pathlib import Path
from backend.app.core.config import settings
from backend.app.models.task import Task, PatchDiff, ExecutionRun, ApprovalGate, ApprovalStatus, GateType
from backend.app.services.review.review_engine import ReviewEngine

@pytest.fixture
def review_setup(client, db_session):
    orig_dir = settings.resolved_workspace_root / "review_orig_repo"
    orig_dir.mkdir(parents=True, exist_ok=True)
    auth_file = orig_dir / "auth.py"
    initial_content = "def authenticate():\n    return False\n"
    auth_file.write_text(initial_content)

    # Isolated dir
    iso_dir = settings.resolved_workspace_root / "isolated" / "review_task_123"
    iso_dir.mkdir(parents=True, exist_ok=True)
    patched_content = "def authenticate():\n    # Verified secure auth\n    return True\n"
    (iso_dir / "auth.py").write_text(patched_content)

    # Workspace & task records
    ws_res = client.post("/api/v1/workspaces/", json={
        "name": "Review WS",
        "path": str(orig_dir)
    })
    ws_id = ws_res.json()["id"]

    task = Task(
        id="review_task_123",
        workspace_id=ws_id,
        title="Review Auth Patch",
        description="Fix auth",
        status="AWAITING_DIFF_APPROVAL",
        isolated_workspace_path=str(iso_dir)
    )
    db_session.add(task)

    diff = PatchDiff(
        task_id=task.id,
        file_path="auth.py",
        original_content=initial_content,
        patched_content=patched_content,
        diff_text="--- a/auth.py\n+++ b/auth.py\n@@ -1,2 +1,3 @@\n def authenticate():\n+    # Verified secure auth\n-    return False\n+    return True\n",
        status="APPLIED"
    )
    db_session.add(diff)

    exec_run = ExecutionRun(
        task_id=task.id,
        phase="FINAL_VERIFICATION",
        command="pytest -v",
        stdout="1 passed in 0.05s",
        stderr="",
        exit_code=0,
        duration_ms=50,
        status="SUCCESS"
    )
    db_session.add(exec_run)
    db_session.commit()

    return task.id, orig_dir, initial_content, patched_content

def test_quality_report_and_export(client, review_setup):
    task_id, orig_dir, _, _ = review_setup

    report_res = client.get(f"/api/v1/review/{task_id}/report")
    assert report_res.status_code == 200
    report = report_res.json()
    assert report["total_files_changed"] == 1
    assert report["static_analysis_passed"] is True
    assert report["test_evidence"]["final_status"] == "SUCCESS"

    export_res = client.get(f"/api/v1/review/{task_id}/export")
    assert export_res.status_code == 200
    assert "--- a/auth.py" in export_res.text

def test_developer_rejection_leaves_repo_untouched(client, review_setup):
    task_id, orig_dir, initial_content, _ = review_setup

    # Reject
    rej_res = client.post(f"/api/v1/review/{task_id}/decision", json={
        "decision": "REJECTED",
        "notes": "Need different approach."
    })
    assert rej_res.status_code == 200
    assert rej_res.json()["status"] == "CANCELLED"

    # Original repo still unchanged
    assert (orig_dir / "auth.py").read_text() == initial_content

def test_developer_approval_and_safe_merge(client, review_setup):
    task_id, orig_dir, initial_content, patched_content = review_setup

    # 1. Unapproved apply must fail
    apply_fail = client.post(f"/api/v1/review/{task_id}/apply")
    assert apply_fail.status_code == 400

    # 2. Approve
    app_res = client.post(f"/api/v1/review/{task_id}/decision", json={
        "decision": "APPROVED",
        "notes": "Changes verified and approved."
    })
    assert app_res.status_code == 200

    # 3. Apply changes to original repository
    apply_res = client.post(f"/api/v1/review/{task_id}/apply")
    assert apply_res.status_code == 200
    assert apply_res.json()["status"] == "COMPLETED"

    # 4. Original repo is now safely updated with verified code!
    assert (orig_dir / "auth.py").read_text() == patched_content

def test_conflict_detection_blocks_apply(client, review_setup):
    task_id, orig_dir, initial_content, _ = review_setup

    # Simulate external edit in original repository
    (orig_dir / "auth.py").write_text("def authenticate():\n    # External user edited this file!\n    return True\n")

    # Check conflicts endpoint
    conflict_res = client.get(f"/api/v1/review/{task_id}/conflicts")
    assert conflict_res.status_code == 200
    assert conflict_res.json()["has_conflicts"] is True

    # Approve
    client.post(f"/api/v1/review/{task_id}/decision", json={"decision": "APPROVED"})

    # Attempt apply must be BLOCKED with 409 Conflict
    apply_blocked = client.post(f"/api/v1/review/{task_id}/apply")
    assert apply_blocked.status_code == 409
    assert "modified externally" in apply_blocked.json()["detail"]

