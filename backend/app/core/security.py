import os
from pathlib import Path
from typing import List, Optional, Union
from fastapi import HTTPException, status
from backend.app.core.config import settings

class SecurityException(HTTPException):
    def __init__(self, detail: str):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)

def validate_safe_path(target_path: Union[str, Path], allowed_roots: Optional[List[str]] = None) -> Path:
    """
    Validate that target_path is within allowed roots and does not exploit symlinks
    or directory traversal attacks.
    """
    try:
        path = Path(target_path).expanduser().resolve()
    except Exception as e:
        raise SecurityException(f"Invalid path syntax: {str(e)}")

    roots = [Path(r).expanduser().resolve() for r in (allowed_roots or settings.ALLOWED_REPO_ROOTS)]
    # Also allow the app workspace root
    roots.append(settings.resolved_workspace_root)

    is_allowed = any(
        path == root or root in path.parents
        for root in roots
    )

    if not is_allowed:
        raise SecurityException(
            f"Access denied: path '{path}' is not within permitted repository roots: {roots}"
        )

    try:
        if not path.exists():
            # Check parent if path is to be created
            parent = path.parent.resolve()
            if not parent.exists():
                raise SecurityException(f"Target path does not exist and parent is invalid: {path}")
    except (PermissionError, OSError) as e:
        raise SecurityException(f"Filesystem access error for path '{path}': {str(e)}")

    return path

def sanitize_command(command_parts: List[str], allowlist: Optional[List[str]] = None) -> List[str]:
    """Ensure command executable is within permissible dev tools and arguments are safe."""
    if not command_parts:
        raise SecurityException("Empty command provided")

    base_cmd = command_parts[0]
    permitted = allowlist or [
        "pytest", "python", "python3", "npm", "node", "git", "vitest",
        "tsc", "ruff", "flake8", "black", "mypy", "make"
    ]

    base_name = Path(base_cmd).name
    is_permitted = (
        base_name in permitted or
        base_name.startswith("python3.") or
        base_name.startswith("python2.")
    )
    if not is_permitted:
        raise SecurityException(f"Command '{base_name}' is not in the permitted execution allowlist: {permitted}")

    return command_parts
