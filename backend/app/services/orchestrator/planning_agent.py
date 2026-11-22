from pathlib import Path
from typing import Optional
import datetime
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from backend.app.models.workspace import Workspace
from backend.app.models.task import (
    Task,
    TaskStatus,
    PlanStep,
    ApprovalGate,
    ApprovalStatus,
    GateType
)
from backend.app.services.repo_intelligence.scanner import RepositoryScanner
from backend.app.services.llm.gateway import (
    get_llm_adapter,
    BaseLLMAdapter,
    LLMConfigurationError,
    ImplementationPlanOutput
)
from backend.app.core.logging import logger

class PlanningAgent:
    """Orchestrates requirement interpretation, context retrieval, and structured plan generation."""

    def __init__(self, db: Session, adapter: Optional[BaseLLMAdapter] = None):
        self.db = db
        self.adapter = adapter or get_llm_adapter()

    def generate_plan(self, task_id: str) -> Task:
        task = self.db.query(Task).filter(Task.id == task_id).first()
        if not task:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

        workspace = self.db.query(Workspace).filter(Workspace.id == task.workspace_id).first()
        if not workspace:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")

        task.status = TaskStatus.PLANNING.value
        task.current_phase = "COLLECTING_CONTEXT"
        self.db.commit()

        try:
            # 1. Inspect repository context
            scanner = RepositoryScanner(Path(workspace.path))
            summary = scanner.scan_summary()
            context_files = scanner.retrieve_context(
                prompt=f"{task.title}\n{task.description}",
                max_tokens=6000,
                max_files=8
            )
            context_payload = [
                {"path": f.relative_path, "content": f.content, "language": f.language}
                for f in context_files
            ]

            # 2. Invoke LLM Gateway for structured plan
            task.current_phase = "GENERATING_STRUCTURED_PLAN"
            self.db.commit()

            plan_output: ImplementationPlanOutput = self.adapter.generate_plan(
                requirement=f"{task.title}\n\n{task.description}",
                repo_summary=summary,
                context_files=context_payload
            )

            # 3. Clear any existing plan steps
            self.db.query(PlanStep).filter(PlanStep.task_id == task.id).delete()
            self.db.query(ApprovalGate).filter(
                ApprovalGate.task_id == task.id,
                ApprovalGate.gate_type == GateType.PLAN.value
            ).delete()

            # 4. Save generated plan steps
            for step_data in plan_output.steps:
                step = PlanStep(
                    task_id=task.id,
                    step_order=step_data.step_order,
                    title=step_data.title,
                    description=step_data.description,
                    target_files=step_data.target_files,
                    risk_level=step_data.risk_level,
                    status="PENDING"
                )
                self.db.add(step)

            # 5. Create Human Approval Gate
            gate = ApprovalGate(
                task_id=task.id,
                gate_type=GateType.PLAN.value,
                proposed_payload=plan_output.model_dump(),
                status=ApprovalStatus.PENDING.value
            )
            self.db.add(gate)

            task.status = TaskStatus.AWAITING_PLAN_APPROVAL.value
            task.current_phase = "AWAITING_HUMAN_APPROVAL"
            task.model_used = getattr(self.adapter, "model", self.adapter.__class__.__name__)
            task.error_summary = None
            self.db.commit()
            self.db.refresh(task)
            return task

        except LLMConfigurationError as err:
            logger.warning(f"Plan generation failed due to unconfigured AI model: {str(err)}")
            task.status = TaskStatus.FAILED.value
            task.current_phase = "UNCONFIGURED_AI_GATEWAY"
            task.error_summary = str(err)
            self.db.commit()
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(err))

        except Exception as err:
            logger.error(f"Error during plan generation for task {task_id}: {str(err)}", exc_info=True)
            task.status = TaskStatus.FAILED.value
            task.current_phase = "PLANNING_ERROR"
            task.error_summary = f"Planning failed: {str(err)}"
            self.db.commit()
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Planning error: {str(err)}")

    def submit_approval(self, task_id: str, decision: str, notes: Optional[str] = None) -> Task:
        task = self.db.query(Task).filter(Task.id == task_id).first()
        if not task:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

        gate = self.db.query(ApprovalGate).filter(
            ApprovalGate.task_id == task.id,
            ApprovalGate.gate_type == GateType.PLAN.value,
            ApprovalGate.status == ApprovalStatus.PENDING.value
        ).first()

        if not gate:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No pending plan approval gate found")

        decision_upper = decision.upper()
        if decision_upper not in ["APPROVED", "REJECTED"]:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Decision must be APPROVED or REJECTED")

        gate.status = decision_upper
        gate.decision_notes = notes
        gate.decided_at = datetime.datetime.now(datetime.timezone.utc)

        if decision_upper == "APPROVED":
            task.status = TaskStatus.CODING.value
            task.current_phase = "PLAN_APPROVED_READY_FOR_CODING"
            # Update plan steps to pending execution
            for step in task.plan_steps:
                step.status = "APPROVED"
        else:
            task.status = TaskStatus.CANCELLED.value
            task.current_phase = "PLAN_REJECTED"

        self.db.commit()
        self.db.refresh(task)
        return task

