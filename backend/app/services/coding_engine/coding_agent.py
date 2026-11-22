from pathlib import Path
from typing import Optional, List
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from backend.app.models.workspace import Workspace
from backend.app.models.task import (
    Task,
    TaskStatus,
    PlanStep,
    PatchDiff
)
from backend.app.services.coding_engine.workspace_isolator import WorkspaceIsolator
from backend.app.services.coding_engine.patch_engine import PatchEngine
from backend.app.services.llm.gateway import (
    get_llm_adapter,
    BaseLLMAdapter,
    LLMConfigurationError,
    CodingOutput
)
from backend.app.core.logging import logger

class CodingAgent:
    """Executes code generation and applies patches within an isolated workspace sandbox."""

    def __init__(self, db: Session, adapter: Optional[BaseLLMAdapter] = None):
        self.db = db
        self.adapter = adapter or get_llm_adapter()
        self.isolator = WorkspaceIsolator()

    def execute_coding(self, task_id: str) -> Task:
        task = self.db.query(Task).filter(Task.id == task_id).first()
        if not task:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

        workspace = self.db.query(Workspace).filter(Workspace.id == task.workspace_id).first()
        if not workspace:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")

        task.status = TaskStatus.CODING.value
        task.current_phase = "CREATING_ISOLATED_WORKSPACE"
        self.db.commit()

        try:
            # 1. Create pristine isolated copy of repository
            isolated_path = self.isolator.create_isolated_copy(task.id, Path(workspace.path))
            task.isolated_workspace_path = str(isolated_path)
            task.current_phase = "GENERATING_CODE_PATCHES"
            self.db.commit()

            # 2. Collect plan steps
            steps = self.db.query(PlanStep).filter(PlanStep.task_id == task.id).order_by(PlanStep.step_order).all()

            for step in steps:
                step.status = "IN_PROGRESS"
                self.db.commit()

                # Read target files from isolated workspace
                context_files = []
                for target_rel in step.target_files:
                    fpath = isolated_path / target_rel
                    if fpath.exists():
                        try:
                            with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                                context_files.append({"path": target_rel, "content": f.read()})
                        except Exception:
                            pass

                # Request code patch from LLM Gateway
                coding_output: CodingOutput = self.adapter.generate_patch(
                    requirement=task.description,
                    plan_step={"order": step.step_order, "title": step.title, "description": step.description},
                    context_files=context_files
                )

                # 3. Apply patches safely through PatchEngine
                for patch in coding_output.patches:
                    orig, patched, diff_text = PatchEngine.apply_patch(isolated_path, patch)

                    # Record PatchDiff
                    diff_record = PatchDiff(
                        task_id=task.id,
                        file_path=patch.file_path,
                        original_content=orig,
                        patched_content=patched,
                        diff_text=diff_text,
                        status="APPLIED"
                    )
                    self.db.add(diff_record)

                step.status = "COMPLETED"
                self.db.commit()

            task.status = TaskStatus.VERIFYING.value
            task.current_phase = "READY_FOR_TEST_VERIFICATION"
            task.error_summary = None
            self.db.commit()
            self.db.refresh(task)
            return task

        except LLMConfigurationError as err:
            logger.warning(f"Coding phase failed due to unconfigured AI model: {str(err)}")
            task.status = TaskStatus.FAILED.value
            task.current_phase = "UNCONFIGURED_AI_GATEWAY"
            task.error_summary = str(err)
            self.db.commit()
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(err))

        except Exception as err:
            logger.error(f"Error during coding phase for task {task_id}: {str(err)}", exc_info=True)
            task.status = TaskStatus.FAILED.value
            task.current_phase = "CODING_ERROR"
            task.error_summary = f"Patch generation error: {str(err)}"
            self.db.commit()
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(err))

    def rollback(self, task_id: str) -> Task:
        task = self.db.query(Task).filter(Task.id == task_id).first()
        if not task:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

        workspace = self.db.query(Workspace).filter(Workspace.id == task.workspace_id).first()
        if not workspace:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")

        # Rollback isolated directory
        self.isolator.rollback(task.id, Path(workspace.path))
        # Remove recorded patches
        self.db.query(PatchDiff).filter(PatchDiff.task_id == task.id).delete()
        task.status = TaskStatus.CODING.value
        task.current_phase = "ISOLATED_WORKSPACE_ROLLED_BACK"
        self.db.commit()
        self.db.refresh(task)
        return task

