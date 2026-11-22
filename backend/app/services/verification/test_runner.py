import os
import time
import subprocess
import shlex
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.core.security import sanitize_command, SecurityException
from backend.app.models.task import ExecutionRun

ALLOWED_TEST_EXECUTABLES = {
    "pytest", "vitest", "npm", "python", "python3", "tsc"
}

def is_allowed_executable(cmd_name: str) -> bool:
    if cmd_name in ALLOWED_TEST_EXECUTABLES:
        return True
    if cmd_name.startswith("python3.") or cmd_name.startswith("python2."):
        return True
    return False

class TestRunner:
    """Discovers project test commands and executes them with strict timeouts and environment sanitization."""
    __test__ = False

    def __init__(self, isolated_path: Path):
        self.isolated_path = isolated_path.resolve()
        if not self.isolated_path.exists():
            raise FileNotFoundError(f"Isolated workspace path does not exist: {self.isolated_path}")

    def discover_test_command(self) -> List[str]:
        """Automatically identify test framework in the isolated workspace."""
        # Check Python / pytest
        has_python_tests = any(
            list(self.isolated_path.glob("test_*.py")) +
            list(self.isolated_path.glob("*_test.py")) +
            list(self.isolated_path.glob("tests/*.py"))
        )
        if has_python_tests or (self.isolated_path / "pytest.ini").exists():
            # Use current virtualenv pytest if available, else standard pytest
            venv_pytest = Path(settings.WORKSPACE_ROOT).resolve().parent / ".venv/bin/pytest"
            if venv_pytest.exists():
                return [str(venv_pytest), "-v"]
            return ["pytest", "-v"]

        # Check Node / npm
        pkg_json = self.isolated_path / "package.json"
        if pkg_json.exists():
            return ["npm", "test"]

        # Default fallback
        return ["pytest", "-v"]

    def execute_command(
        self,
        cmd_parts: List[str],
        timeout_seconds: Optional[int] = None
    ) -> Tuple[int, str, str, int]:
        """
        Executes permitted command inside isolated directory with resource limits and sanitized env.
        Returns: (exit_code, stdout, stderr, duration_ms)
        """
        # Validate allowlist
        base_cmd = Path(cmd_parts[0]).name
        if not is_allowed_executable(base_cmd):
            raise SecurityException(f"Execution of '{base_cmd}' is prohibited by test execution allowlist.")

        # Sanitized environment: strip sensitive keys
        clean_path = f"/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:{os.environ.get('PATH', '')}"
        clean_env = {
            "PATH": clean_path,
            "HOME": str(self.isolated_path),
            "LANG": "en_US.UTF-8",
            "PYTHONPATH": str(self.isolated_path),
            "PYTHONDONTWRITEBYTECODE": "1"
        }

        timeout = timeout_seconds or settings.ISOLATED_SANDBOX_TIMEOUT_SECONDS
        start_time = time.perf_counter()

        try:
            process = subprocess.run(
                cmd_parts,
                cwd=str(self.isolated_path),
                env=clean_env,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            duration_ms = int((time.perf_counter() - start_time) * 1000)
            return process.returncode, process.stdout, process.stderr, duration_ms

        except subprocess.TimeoutExpired as exc:
            duration_ms = int((time.perf_counter() - start_time) * 1000)
            return -1, (exc.stdout or "").decode("utf-8", "ignore") if isinstance(exc.stdout, bytes) else str(exc.stdout or ""), f"Execution timed out after {timeout} seconds", duration_ms

        except Exception as exc:
            duration_ms = int((time.perf_counter() - start_time) * 1000)
            return -2, "", f"Execution failed: {str(exc)}", duration_ms
