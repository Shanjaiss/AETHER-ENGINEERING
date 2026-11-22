import difflib
from pathlib import Path
from typing import Tuple
from backend.app.services.llm.gateway import PatchFileOutput
from backend.app.core.security import SecurityException
from backend.app.core.logging import logger

class PatchEngine:
    """Validates, applies, and tracks source code modifications within isolated workspaces."""

    @staticmethod
    def validate_patch(isolated_root: Path, patch: PatchFileOutput) -> Tuple[bool, str]:
        """Verify patch targets safe boundaries and valid files."""
        if "\x00" in patch.file_path:
            return False, "Null bytes in file path are strictly prohibited."

        try:
            raw_path = isolated_root / patch.file_path
            target_path = raw_path.resolve()
            parent_path = (isolated_root / Path(patch.file_path).parent).resolve()
        except Exception as e:
            return False, f"Invalid path syntax: {str(e)}"

        # Strict boundary enforcement: target and parent MUST be inside isolated_root
        if isolated_root != target_path and isolated_root not in target_path.parents:
            return False, f"Directory traversal violation: '{patch.file_path}' escapes sandbox."

        if isolated_root != parent_path and isolated_root not in parent_path.parents:
            return False, f"Parent traversal violation: '{patch.file_path}' escapes sandbox."

        # Prevent symlink manipulation
        if raw_path.is_symlink():
            return False, f"Targeting symlink '{patch.file_path}' is strictly prohibited."

        # Forbidden filenames
        name = target_path.name
        if (
            name.startswith(".env") or
            name.startswith("id_") or
            name.endswith((".key", ".pem", ".cert", ".p8", ".p12", ".pfx"))
        ):
            return False, f"Targeting sensitive file '{name}' is forbidden."

        if patch.action == "modify" and not target_path.is_file():
            return False, f"Cannot modify non-existent file: '{patch.file_path}'"

        return True, "Valid"

    @classmethod
    def apply_patch(cls, isolated_root: Path, patch: PatchFileOutput) -> Tuple[str, str, str]:
        """
        Applies a validated patch to the target file inside isolated_root.
        Returns: (original_content, patched_content, unified_diff_text)
        """
        is_valid, reason = cls.validate_patch(isolated_root, patch)
        if not is_valid:
            raise SecurityException(f"Patch validation failed for '{patch.file_path}': {reason}")

        target_path = (isolated_root / patch.file_path).resolve()
        original_content = ""

        if patch.action == "create":
            if target_path.exists():
                with open(target_path, "r", encoding="utf-8", errors="replace") as f:
                    original_content = f.read()
            else:
                target_path.parent.mkdir(parents=True, exist_ok=True)
            patched_content = patch.diff_or_content
        elif patch.action == "modify":
            with open(target_path, "r", encoding="utf-8", errors="replace") as f:
                original_content = f.read()

            # If diff_or_content is replacement content:
            patched_content = patch.diff_or_content
        else:
            raise ValueError(f"Unsupported patch action: {patch.action}")

        # Write to isolated copy
        with open(target_path, "w", encoding="utf-8") as f:
            f.write(patched_content)

        # Compute standard unified diff
        orig_lines = original_content.splitlines(keepends=True)
        patched_lines = patched_content.splitlines(keepends=True)
        diff_lines = list(difflib.unified_diff(
            orig_lines,
            patched_lines,
            fromfile=f"a/{patch.file_path}",
            tofile=f"b/{patch.file_path}",
            n=3
        ))
        diff_text = "".join(diff_lines)

        logger.info(f"Applied patch to {patch.file_path} ({len(diff_lines)} diff lines)")
        return original_content, patched_content, diff_text
