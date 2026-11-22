from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from backend.app.models.task import Task, PatchDiff, ExecutionRun, PlanStep
from backend.app.services.orchestrator.task_memory import TaskMemoryManager

class QualityEvaluationResult(BaseModel):
    task_id: str
    acceptance_criteria_passed: List[str] = Field(default_factory=list)
    acceptance_criteria_unmet: List[str] = Field(default_factory=list)
    unnecessary_files_modified: List[str] = Field(default_factory=list)
    has_test_evidence: bool
    is_approved_for_merge: bool
    retry_justified: bool
    reflection_notes: str

class QualityController:
    """Evidence-based reflection and quality control engine. Validates real test evidence,

    detects extraneous modifications, and prevents endless reflection loops.
    """

    def __init__(self, db: Session):
        self.db = db

    def evaluate_task(self, task_id: str, max_repair_retries: int = 3) -> QualityEvaluationResult:
        task = self.db.query(Task).filter(Task.id == task_id).first()
        if not task:
            raise ValueError(f"Task {task_id} not found")

        patches = self.db.query(PatchDiff).filter(PatchDiff.task_id == task_id).all()
        plan_steps = self.db.query(PlanStep).filter(PlanStep.task_id == task_id).all()
        executions = self.db.query(ExecutionRun).filter(ExecutionRun.task_id == task_id).order_by(ExecutionRun.created_at.desc()).all()

        # 1. Approved target files from plan
        approved_target_files = set()
        for s in plan_steps:
            for tf in s.target_files:
                approved_target_files.add(tf)

        # 2. Check for unnecessary modifications outside plan
        unnecessary = []
        for p in patches:
            if approved_target_files and p.file_path not in approved_target_files:
                unnecessary.append(p.file_path)

        # 3. Check real test evidence
        latest_exec = executions[0] if executions else None
        test_passed = bool(latest_exec and latest_exec.exit_code == 0)

        # 4. Acceptance criteria verification
        ac_passed = []
        ac_unmet = []

        if test_passed:
            ac_passed.append("Automated verification tests execute and pass with exit code 0")
        else:
            ac_unmet.append("Automated verification tests failed or have not been executed")

        if len(patches) > 0 and len(unnecessary) == 0:
            ac_passed.append(f"Targeted modifications restricted strictly to planned files ({len(patches)} files)")
        elif unnecessary:
            ac_unmet.append(f"Extraneous files modified outside approved plan: {', '.join(unnecessary)}")

        # 5. Determine if further repair is justified
        current_attempts = task.repair_attempts
        retry_justified = (not test_passed) and (current_attempts < max_repair_retries)

        # 6. Final merge eligibility
        is_ready = test_passed and len(unnecessary) == 0 and len(patches) > 0

        # 7. Formulate reflection notes based on real evidence
        if is_ready:
            notes = (
                f"Quality verification PASSED. {len(patches)} file(s) modified with zero extraneous files. "
                f"Test execution succeeded in {latest_exec.duration_ms if latest_exec else 0}ms. Ready for final developer review."
            )
        elif not test_passed:
            notes = (
                f"Quality verification FAILED: Test execution exited with code {latest_exec.exit_code if latest_exec else 'N/A'}. "
                f"Repair attempts: {current_attempts}/{max_repair_retries}. Retry justified: {retry_justified}."
            )
        else:
            notes = f"Quality verification INCOMPLETE: {'; '.join(ac_unmet)}"

        # Record empirical fact in memory
        TaskMemoryManager.record_fact(
            task_id,
            f"Quality reflection: Test passed={test_passed}, Extraneous files={len(unnecessary)}, Ready={is_ready}",
            source="QUALITY_CONTROLLER"
        )

        return QualityEvaluationResult(
            task_id=task_id,
            acceptance_criteria_passed=ac_passed,
            acceptance_criteria_unmet=ac_unmet,
            unnecessary_files_modified=unnecessary,
            has_test_evidence=test_passed,
            is_approved_for_merge=is_ready,
            retry_justified=retry_justified,
            reflection_notes=notes
        )

