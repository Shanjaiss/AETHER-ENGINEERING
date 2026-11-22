import ast
import datetime
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from backend.app.models.workspace import Workspace
from backend.app.models.task import (
    Task,
    TaskStatus,
    PatchDiff,
    ExecutionRun,
    ApprovalGate,
    ApprovalStatus,
    GateType
)
from backend.app.schemas.review import (
    QualityReportResponse,
    ChangedFileMetric,
    ConflictCheckResponse
)
from backend.app.core.logging import SECRET_PATTERNS, logger
from backend.app.core.security import SecurityException

SUSPICIOUS_PATTERNS = ["eval(", "exec(", "__import__(", "os.system(", "shell=True"]

class ReviewEngine:
    """Provides engineering quality metrics, conflict detection, and safe patch application to source."""

    def __init__(self, db: Session):
        self.db = db

    def generate_quality_report(self, task_id: str) -> QualityReportResponse:
        task = self.db.query(Task).filter(Task.id == task_id).first()
        if not task:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

        patches = self.db.query(PatchDiff).filter(PatchDiff.task_id == task.id).all()
        executions = self.db.query(ExecutionRun).filter(ExecutionRun.task_id == task.id).order_by(ExecutionRun.created_at.desc()).all()

        total_added = 0
        total_removed = 0
        changed_metrics: List[ChangedFileMetric] = []
        security_warnings: List[str] = []
        static_analysis_ok = True

        for p in patches:
            added = 0
            removed = 0
            for line in p.diff_text.splitlines():
                if line.startswith("+") and not line.startswith("+++"):
                    added += 1
                elif line.startswith("-") and not line.startswith("---"):
                    removed += 1

            total_added += added
            total_removed += removed

            # Static syntax validation for Python
            if p.file_path.endswith(".py") and p.patched_content:
                try:
                    ast.parse(p.patched_content)
                except SyntaxError as e:
                    static_analysis_ok = False
                    security_warnings.append(f"Syntax error in {p.file_path}: {str(e)}")

            # Check suspicious functions or secrets
            if p.patched_content:
                for susp in SUSPICIOUS_PATTERNS:
                    if susp in p.patched_content:
                        security_warnings.append(f"Potentially dangerous pattern '{susp}' detected in {p.file_path}")
                for pattern in SECRET_PATTERNS:
                    if pattern.search(p.patched_content):
                        security_warnings.append(f"Possible credential pattern detected in {p.file_path}")

            risk = "LOW"
            if added > 100 or removed > 50 or "auth" in p.file_path.lower() or "security" in p.file_path.lower():
                risk = "MEDIUM"
            if len(security_warnings) > 0:
                risk = "HIGH"

            changed_metrics.append(ChangedFileMetric(
                file_path=p.file_path,
                lines_added=added,
                lines_removed=removed,
                risk_level=risk
            ))

        overall_risk = "LOW"
        if any(m.risk_level == "HIGH" for m in changed_metrics) or not static_analysis_ok:
            overall_risk = "HIGH"
        elif any(m.risk_level == "MEDIUM" for m in changed_metrics) or total_added > 50:
            overall_risk = "MEDIUM"

        latest_exec = executions[0] if executions else None
        test_evidence = {
            "total_runs": len(executions),
            "final_status": latest_exec.status if latest_exec else "NO_TESTS_RUN",
            "last_exit_code": latest_exec.exit_code if latest_exec else None,
            "duration_ms": latest_exec.duration_ms if latest_exec else 0
        }

        return QualityReportResponse(
            task_id=task.id,
            total_files_changed=len(patches),
            total_lines_added=total_added,
            total_lines_removed=total_removed,
            overall_risk=overall_risk,
            security_warnings=security_warnings,
            static_analysis_passed=static_analysis_ok,
            test_evidence=test_evidence,
            changed_files=changed_metrics,
            summary=f"Generated {len(patches)} patch(es) (+{total_added}/-{total_removed} lines). Verified passing tests: {test_evidence['final_status']}."
        )

    def detect_conflicts(self, task_id: str) -> ConflictCheckResponse:
        task = self.db.query(Task).filter(Task.id == task_id).first()
        if not task:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

        workspace = self.db.query(Workspace).filter(Workspace.id == task.workspace_id).first()
        if not workspace:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")

        orig_root = Path(workspace.path)
        patches = self.db.query(PatchDiff).filter(PatchDiff.task_id == task.id).all()

        conflicts: List[str] = []
        for p in patches:
            orig_file = orig_root / p.file_path
            if orig_file.exists():
                try:
                    current_content = orig_file.read_text(encoding="utf-8", errors="replace")
                    if p.original_content is not None and current_content != p.original_content:
                        conflicts.append(f"{p.file_path} was modified externally in the original repository.")
                except Exception as e:
                    conflicts.append(f"Error inspecting {p.file_path}: {str(e)}")

        has_conflicts = len(conflicts) > 0
        return ConflictCheckResponse(
            has_conflicts=has_conflicts,
            conflicted_files=conflicts,
            message="Conflicts detected with original repository" if has_conflicts else "Clean: no external modifications detected."
        )

    def submit_review_decision(self, task_id: str, decision: str, notes: Optional[str] = None) -> Task:
        task = self.db.query(Task).filter(Task.id == task_id).first()
        if not task:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

        decision_upper = decision.upper()
        if decision_upper not in ["APPROVED", "REJECTED"]:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Decision must be APPROVED or REJECTED")

        # Create or update diff approval gate
        gate = self.db.query(ApprovalGate).filter(
            ApprovalGate.task_id == task.id,
            ApprovalGate.gate_type == GateType.DIFF.value
        ).first()

        if not gate:
            gate = ApprovalGate(
                task_id=task.id,
                gate_type=GateType.DIFF.value,
                status=decision_upper,
                decision_notes=notes,
                decided_at=datetime.datetime.now(datetime.timezone.utc)
            )
            self.db.add(gate)
        else:
            gate.status = decision_upper
            gate.decision_notes = notes
            gate.decided_at = datetime.datetime.now(datetime.timezone.utc)

        if decision_upper == "REJECTED":
            task.status = TaskStatus.CANCELLED.value
            task.current_phase = "CHANGES_REJECTED_BY_DEVELOPER"
        else:
            task.current_phase = "CHANGES_APPROVED_READY_TO_APPLY"

        self.db.commit()
        self.db.refresh(task)
        return task

    def apply_approved_patches(self, task_id: str) -> Task:
        task = self.db.query(Task).filter(Task.id == task_id).first()
        if not task:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

        workspace = self.db.query(Workspace).filter(Workspace.id == task.workspace_id).first()
        if not workspace:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")

        # Guard against duplicate concurrent application
        if task.status == TaskStatus.COMPLETED.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Task has already been merged and completed."
            )

        # 1. Verify conflict status
        conflict_status = self.detect_conflicts(task.id)
        if conflict_status.has_conflicts:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Cannot apply patch: original repository has been modified externally: {conflict_status.conflicted_files}"
            )

        # 2. Check gate approval
        gate = self.db.query(ApprovalGate).filter(
            ApprovalGate.task_id == task.id,
            ApprovalGate.gate_type == GateType.DIFF.value,
            ApprovalGate.status == ApprovalStatus.APPROVED.value
        ).first()

        if not gate:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Developer approval is strictly required before applying changes to the original repository."
            )

        orig_root = Path(workspace.path)
        isolated_root = Path(task.isolated_workspace_path)
        patches = self.db.query(PatchDiff).filter(PatchDiff.task_id == task.id).all()

        # 3. Apply changes to original repository
        for p in patches:
            src_file = isolated_root / p.file_path
            dst_file = orig_root / p.file_path

            if not src_file.exists():
                raise HTTPException(status_code=500, detail=f"Patched file missing in isolated workspace: {p.file_path}")

            dst_file.parent.mkdir(parents=True, exist_ok=True)
            with open(src_file, "r", encoding="utf-8") as rf:
                content = rf.read()
            with open(dst_file, "w", encoding="utf-8") as wf:
                wf.write(content)

            p.status = "MERGED_TO_SOURCE"

        task.status = TaskStatus.COMPLETED.value
        task.current_phase = "MERGED_TO_SOURCE_REPOSITORY"
        self.db.commit()
        self.db.refresh(task)
        logger.info(f"Successfully applied approved patch for task {task.id} to original repository {orig_root}")
        return task

    def export_patch(self, task_id: str) -> str:
        patches = self.db.query(PatchDiff).filter(PatchDiff.task_id == task_id).all()
        return "\n\n".join(p.diff_text for p in patches)

