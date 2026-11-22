import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable
from pydantic import BaseModel, Field

from backend.app.core.security import validate_safe_path, SecurityException, sanitize_command
from backend.app.core.logging import logger
from backend.app.services.repo_intelligence.scanner import RepositoryScanner
from backend.app.services.coding_engine.patch_engine import PatchEngine
from backend.app.services.verification.test_runner import TestRunner
from backend.app.services.llm.gateway import PatchFileOutput
from backend.app.services.orchestrator.task_memory import TaskMemoryManager

class ToolDefinition(BaseModel):
    name: str
    description: str
    requires_approval: bool = False
    parameter_schema: Dict[str, Any]

class ToolResult(BaseModel):
    tool_name: str
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    duration_ms: int = 0

class ToolRegistry:
    """Central typed registry for application-controlled engineering tools enforcing

    strict path boundaries, command allowlists, and execution audits.
    """

    def __init__(self, workspace_path: Path, task_id: str, is_plan_approved: bool = False):
        self.workspace_path = validate_safe_path(workspace_path)
        self.task_id = task_id
        self.is_plan_approved = is_plan_approved
        self.scanner = RepositoryScanner(self.workspace_path)

    def execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> ToolResult:
        start_time = time.perf_counter()
        tool_fn = getattr(self, f"tool_{tool_name}", None)

        if not tool_fn:
            duration_ms = int((time.perf_counter() - start_time) * 1000)
            return ToolResult(
                tool_name=tool_name,
                success=False,
                error=f"Unrecognized tool: '{tool_name}'",
                duration_ms=duration_ms
            )

        try:
            res_data = tool_fn(**parameters)
            duration_ms = int((time.perf_counter() - start_time) * 1000)

            TaskMemoryManager.record_tool_call(
                task_id=self.task_id,
                tool_name=tool_name,
                arguments=parameters,
                exit_code=0,
                duration_ms=duration_ms,
                output_summary=str(res_data)[:200]
            )

            return ToolResult(
                tool_name=tool_name,
                success=True,
                data=res_data,
                duration_ms=duration_ms
            )

        except SecurityException as sec_err:
            duration_ms = int((time.perf_counter() - start_time) * 1000)
            logger.warning(f"Security boundary triggered in tool {tool_name}: {sec_err.detail}")
            return ToolResult(
                tool_name=tool_name,
                success=False,
                error=f"Security violation: {sec_err.detail}",
                duration_ms=duration_ms
            )
        except Exception as err:
            duration_ms = int((time.perf_counter() - start_time) * 1000)
            logger.error(f"Error executing tool {tool_name}: {err}", exc_info=True)
            return ToolResult(
                tool_name=tool_name,
                success=False,
                error=str(err),
                duration_ms=duration_ms
            )

    # 1. read_permitted_file
    def tool_read_permitted_file(self, file_path: str) -> Dict[str, Any]:
        return self.scanner.read_safe_file(file_path)

    # 2. search_repository
    def tool_search_repository(self, query: str, max_results: int = 20) -> Dict[str, Any]:
        results = self.scanner.search_code(query=query, max_results=max_results)
        return {"query": query, "matches": [r.model_dump() for r in results]}

    # 3. locate_symbol
    def tool_locate_symbol(self, symbol_name: str) -> Dict[str, Any]:
        call_sites = self.scanner.locate_call_sites(symbol_name)
        return {
            "symbol": symbol_name,
            "call_sites": [cs.model_dump() for cs in call_sites]
        }

    # 4. validate_patch
    def tool_validate_patch(self, file_path: str, action: str, content: str) -> Dict[str, Any]:
        patch = PatchFileOutput(
            file_path=file_path,
            action=action,
            diff_or_content=content,
            explanation="Tool validation check"
        )
        is_valid, reason = PatchEngine.validate_patch(self.workspace_path, patch)
        return {"is_valid": is_valid, "reason": reason, "file_path": file_path}

    # 5. apply_isolated_patch (Privileged)
    def tool_apply_isolated_patch(self, isolated_root: str, file_path: str, action: str, content: str) -> Dict[str, Any]:
        if not self.is_plan_approved:
            raise SecurityException("Privileged operation denied: Plan approval is required before applying patches.")

        iso_path = validate_safe_path(isolated_root)
        patch = PatchFileOutput(
            file_path=file_path,
            action=action,
            diff_or_content=content,
            explanation="Tool isolated modification"
        )
        orig, patched, diff_text = PatchEngine.apply_patch(iso_path, patch)
        return {
            "file_path": file_path,
            "diff_text": diff_text,
            "lines_changed": len(diff_text.splitlines())
        }

    # 6. execute_permitted_verification (Privileged)
    def tool_execute_permitted_verification(self, isolated_root: str, command: Optional[List[str]] = None, timeout_seconds: int = 30) -> Dict[str, Any]:
        iso_path = validate_safe_path(isolated_root)
        runner = TestRunner(iso_path)
        cmd_parts = command or runner.discover_test_command()
        exit_code, stdout, stderr, dur_ms = runner.execute_command(cmd_parts, timeout_seconds=timeout_seconds)
        return {
            "command": " ".join(cmd_parts),
            "exit_code": exit_code,
            "passed": exit_code == 0,
            "stdout": stdout,
            "stderr": stderr,
            "duration_ms": dur_ms
        }

    # 7. create_engineering_report
    def tool_create_engineering_report(self, task_summary: str, files_modified: List[str], test_passed: bool) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "summary": task_summary,
            "files_modified": files_modified,
            "verified_passing": test_passed,
            "verification_source": "Sandboxed TestRunner"
        }

