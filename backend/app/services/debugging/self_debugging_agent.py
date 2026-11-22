from pathlib import Path
from typing import Optional, List
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.models.task import (
    Task,
    TaskStatus,
    ExecutionRun,
    PatchDiff
)
from backend.app.services.verification.test_runner import TestRunner
from backend.app.services.debugging.failure_classifier import FailureClassifier
from backend.app.services.coding_engine.patch_engine import PatchEngine
from backend.app.services.llm.gateway import (
    get_llm_adapter,
    BaseLLMAdapter,
    LLMConfigurationError,
    CodingOutput
)

class SelfDebuggingAgent:
    """Orchestrates test verification, failure classification, and bounded autonomous repairs."""

    def __init__(self, db: Session, adapter: Optional[BaseLLMAdapter] = None):
        self.db = db
        self.adapter = adapter or get_llm_adapter()

    def verify_and_repair(self, task_id: str) -> Task:
        task = self.db.query(Task).filter(Task.id == task_id).first()
        if not task:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

        if not task.isolated_workspace_path or not Path(task.isolated_workspace_path).exists():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Task does not have an active isolated workspace. Execute coding phase first."
            )

        isolated_path = Path(task.isolated_workspace_path)
        runner = TestRunner(isolated_path)
        test_cmd = runner.discover_test_command()

        max_attempts = settings.MAX_REPAIR_ATTEMPTS

        while True:
            current_attempt = task.repair_attempts + 1
            task.status = TaskStatus.VERIFYING.value
            task.current_phase = f"TEST_VERIFICATION_RUN_{current_attempt}"
            self.db.commit()

            # Execute permitted tests
            exit_code, stdout, stderr, duration_ms = runner.execute_command(test_cmd)

            # Record ExecutionRun
            exec_record = ExecutionRun(
                task_id=task.id,
                phase=f"TEST_VERIFICATION_{current_attempt}",
                command=" ".join(test_cmd),
                stdout=stdout,
                stderr=stderr,
                exit_code=exit_code,
                duration_ms=duration_ms,
                status="SUCCESS" if exit_code == 0 else "FAILURE"
            )
            self.db.add(exec_record)
            self.db.commit()

            # Case A: Tests Passed
            if exit_code == 0:
                logger.info(f"Task {task.id} successfully passed verification on attempt {current_attempt}!")
                task.status = TaskStatus.AWAITING_DIFF_APPROVAL.value
                task.current_phase = "VERIFIED_ALL_TESTS_PASSED"
                task.error_summary = None
                self.db.commit()
                self.db.refresh(task)
                return task

            # Case B: Failure detected -> Classify and diagnose
            diagnosis = FailureClassifier.classify(stdout, stderr, exit_code)
            logger.warning(f"Verification failure on task {task.id}: {diagnosis['category']} - {diagnosis['summary']}")

            if task.repair_attempts >= max_attempts:
                task.status = TaskStatus.FAILED.value
                task.current_phase = "MAX_REPAIR_ATTEMPTS_EXCEEDED"
                task.error_summary = f"Verification failed after {task.repair_attempts} repairs. Diagnosis: {diagnosis['summary']}"
                self.db.commit()
                self.db.refresh(task)
                return task

            # Attempt repair
            task.repair_attempts += 1
            task.status = TaskStatus.DEBUGGING.value
            task.current_phase = f"SELF_DEBUGGING_REPAIR_{task.repair_attempts}"
            self.db.commit()

            # Collect source files for repair context
            context_files = []
            for item in isolated_path.glob("*.py"):
                try:
                    with open(item, "r", encoding="utf-8", errors="ignore") as f:
                        context_files.append({"path": item.name, "content": f.read()})
                except Exception:
                    pass

            try:
                repair_output: CodingOutput = self.adapter.diagnose_and_repair(
                    requirement=task.description,
                    failed_command=" ".join(test_cmd),
                    stdout=stdout,
                    stderr=stderr,
                    context_files=context_files
                )

                if not repair_output.patches:
                    task.status = TaskStatus.FAILED.value
                    task.current_phase = "NO_REPAIR_PATCH_PROPOSED"
                    task.error_summary = f"Self-debugging agent could not formulate a repair patch for {diagnosis['category']}."
                    self.db.commit()
                    return task

                # Apply repair patches
                for patch in repair_output.patches:
                    orig, patched, diff_text = PatchEngine.apply_patch(isolated_path, patch)

                    # Update or append PatchDiff
                    existing_diff = self.db.query(PatchDiff).filter(
                        PatchDiff.task_id == task.id,
                        PatchDiff.file_path == patch.file_path
                    ).first()

                    if existing_diff:
                        existing_diff.patched_content = patched
                        existing_diff.diff_text = diff_text
                    else:
                        new_diff = PatchDiff(
                            task_id=task.id,
                            file_path=patch.file_path,
                            original_content=orig,
                            patched_content=patched,
                            diff_text=diff_text,
                            status="APPLIED"
                        )
                        self.db.add(new_diff)

                self.db.commit()
                logger.info(f"Applied self-debugging repair iteration {task.repair_attempts} for task {task.id}")

            except LLMConfigurationError as err:
                task.status = TaskStatus.FAILED.value
                task.current_phase = "UNCONFIGURED_AI_GATEWAY"
                task.error_summary = str(err)
                self.db.commit()
                raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(err))

            except Exception as err:
                logger.error(f"Error during repair proposal: {str(err)}", exc_info=True)
                task.status = TaskStatus.FAILED.value
                task.current_phase = "REPAIR_ERROR"
                task.error_summary = f"Repair failed: {str(err)}"
                self.db.commit()
                return task

