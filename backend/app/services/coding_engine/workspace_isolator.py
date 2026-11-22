import os
import shutil
from pathlib import Path
from typing import Optional
from backend.app.core.config import settings
from backend.app.core.security import validate_safe_path, SecurityException
from backend.app.core.logging import logger

class WorkspaceIsolator:
    """Manages secure isolated working copies for autonomous agent modifications."""

    def __init__(self, base_isolated_root: Optional[Path] = None):
        self.base_root = base_isolated_root or (settings.resolved_workspace_root / "isolated")
        self.base_root.mkdir(parents=True, exist_ok=True)

    def create_isolated_copy(self, task_id: str, source_path: Path) -> Path:
        """
        Creates a sandboxed copy of the source repository for a specific task.
        Guarantees original repository is never modified during agent operations.
        """
        source = validate_safe_path(source_path)
        isolated_dir = self.base_root / task_id

        if isolated_dir.exists():
            shutil.rmtree(isolated_dir)

        # Ignore heavy or sensitive dirs during copy
        def _ignore_patterns(path, names):
            ignored = set()
            for name in names:
                if name in [".git", "node_modules", ".venv", "venv", "__pycache__", ".pytest_cache", "dist", "build"]:
                    ignored.add(name)
                elif name.startswith(".env") or name.endswith((".key", ".pem")):
                    ignored.add(name)
            return ignored

        shutil.copytree(source, isolated_dir, ignore=_ignore_patterns, symlinks=False)
        logger.info(f"Created isolated workspace for task {task_id} at {isolated_dir}")
        return isolated_dir

    def get_isolated_path(self, task_id: str) -> Optional[Path]:
        path = self.base_root / task_id
        return path if path.exists() else None

    def rollback(self, task_id: str, source_path: Path) -> Path:
        """Reset the isolated workspace to a pristine copy of original repository."""
        return self.create_isolated_copy(task_id, source_path)

    def cleanup(self, task_id: str) -> None:
        """Remove isolated workspace directory."""
        path = self.get_isolated_path(task_id)
        if path and path.exists():
            shutil.rmtree(path)
            logger.info(f"Cleaned up isolated workspace for task {task_id}")
