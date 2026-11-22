import pytest
import logging
from pathlib import Path
from backend.app.core.security import validate_safe_path, SecurityException
from backend.app.core.logging import SecretRedactingFormatter, SECRET_PATTERNS
from backend.app.services.verification.test_runner import TestRunner
from backend.app.services.coding_engine.patch_engine import PatchEngine
from backend.app.services.llm.gateway import PatchFileOutput

def test_directory_traversal_rejections():
    with pytest.raises(SecurityException):
        validate_safe_path("/etc/passwd")

    with pytest.raises(SecurityException):
        validate_safe_path("/var/root")

def test_patch_engine_rejects_escape(tmp_path):
    sandbox = tmp_path / "sandbox"
    sandbox.mkdir()

    # Traversal in patch path
    bad_patch = PatchFileOutput(
        file_path="../../etc/shadow",
        action="modify",
        diff_or_content="bad",
        explanation="exploit"
    )
    is_valid, reason = PatchEngine.validate_patch(sandbox, bad_patch)
    assert is_valid is False
    assert "Directory traversal" in reason

    # Sensitive file target
    env_patch = PatchFileOutput(
        file_path=".env",
        action="create",
        diff_or_content="KEY=123",
        explanation="exploit"
    )
    is_valid_env, reason_env = PatchEngine.validate_patch(sandbox, env_patch)
    assert is_valid_env is False
    assert "forbidden" in reason_env

def test_test_runner_command_allowlist_enforcement(tmp_path):
    runner = TestRunner(tmp_path)
    # Prohibited commands
    with pytest.raises(SecurityException):
        runner.execute_command(["rm", "-rf", "/"])

    with pytest.raises(SecurityException):
        runner.execute_command(["curl", "http://malicious.com"])

    with pytest.raises(SecurityException):
        runner.execute_command(["bash", "-c", "echo exploit"])

def test_secret_redacting_formatter():
    formatter = SecretRedactingFormatter("%(message)s")
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="",
        lineno=1,
        msg="Connecting with api_key=sk-12345678901234567890 and Bearer AIzaSyD9876543210123456789012345678901",
        args=(),
        exc_info=None
    )
    formatted = formatter.format(record)
    assert "sk-12345678901234567890" not in formatted
    assert "***REDACTED***" in formatted or "***REDACTED_SECRET***" in formatted

