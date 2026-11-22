from enum import Enum
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from pydantic import BaseModel, Field

from backend.app.models.workspace import Workspace
from backend.app.models.task import (
    Task,
    TaskStatus,
    PlanStep,
    ApprovalGate,
    ApprovalStatus,
    GateType,
    ExecutionRun,
    PatchDiff
)
from backend.app.schemas.task_understanding import TaskUnderstandingResult
from backend.app.schemas.planning import DynamicPlanOutput, DynamicPlanStep
from backend.app.services.task_understanding.task_analyzer import TaskUnderstandingEngine
from backend.app.services.repo_intelligence.scanner import RepositoryScanner
from backend.app.services.orchestrator.dynamic_planner import DynamicPlanner
from backend.app.services.orchestrator.task_memory import TaskMemoryManager
from backend.app.services.coding_engine.workspace_isolator import WorkspaceIsolator
from backend.app.services.coding_engine.patch_engine import PatchEngine
from backend.app.services.verification.test_runner import TestRunner
from backend.app.services.debugging.failure_classifier import FailureClassifier
from backend.app.services.debugging.self_debugging_agent import SelfDebuggingAgent
from backend.app.services.review.review_engine import ReviewEngine
from backend.app.services.llm.gateway import (
    get_llm_adapter,
    BaseLLMAdapter,
    LLMConfigurationError,
    PatchFileOutput
)
from backend.app.core.security import SecurityException
from backend.app.core.logging import logger

class AgentRole(str, Enum):
    REPO_ANALYSIS = "REPO_ANALYSIS"
    PLANNING = "PLANNING"
    CODING = "CODING"
    TESTING = "TESTING"
    DEBUGGING = "DEBUGGING"
    CODE_REVIEW = "CODE_REVIEW"

class AgentTaskState(BaseModel):
    task_id: str
    workspace_id: str
    current_role: AgentRole = AgentRole.REPO_ANALYSIS
    current_phase: str = "INITIALIZED"
    is_plan_approved: bool = False
    is_diff_approved: bool = False
    isolated_workspace_path: Optional[str] = None
    applied_patches_count: int = 0
    test_passed: bool = False
    repair_attempts: int = 0
    error: Optional[str] = None

class SpecializedAgentOrchestrator:
    """Coordinates specialized engineering agent roles within a validated state machine,

    enforcing privilege boundaries before privileged actions.
    """

    def __init__(self, db: Session, adapter: Optional[BaseLLMAdapter] = None):
        self.db = db
        self.adapter = adapter or get_llm_adapter()

    def _get_task_and_workspace(self, task_id: str) -> Tuple[Task, Workspace]:
        task = self.db.query(Task).filter(Task.id == task_id).first()
        if not task:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
        workspace = self.db.query(Workspace).filter(Workspace.id == task.workspace_id).first()
        if not workspace:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")
        return task, workspace

    # 1. Role: Repository Analysis Agent
    def run_repo_analysis(self, task_id: str) -> Dict[str, Any]:
        task, workspace = self._get_task_and_workspace(task_id)
        task.current_phase = "ANALYZING_REPOSITORY"
        self.db.commit()

        scanner = RepositoryScanner(Path(workspace.path))
        summary = scanner.scan_summary()
        dep_graph = scanner.build_dependency_graph()

        TaskMemoryManager.record_fact(
            task_id,
            f"Repository '{summary['name']}' indexed with {summary['file_count']} files, {len(dep_graph.edges)} dependency edges."
        )

        return {
            "summary": summary,
            "dependency_edge_count": len(dep_graph.edges),
            "isolated_files_count": len(dep_graph.isolated_files)
        }

    # 2. Role: Planning Agent
    def run_planning(self, task_id: str) -> DynamicPlanOutput:
        task, workspace = self._get_task_and_workspace(task_id)
        task.status = TaskStatus.PLANNING.value
        task.current_phase = "GENERATING_DYNAMIC_PLAN"
        self.db.commit()

        scanner = RepositoryScanner(Path(workspace.path))
        all_files = scanner.list_repo_files()

        # Task Understanding
        understanding = TaskUnderstandingEngine.analyze(
            title=task.title,
            description=task.description,
            repo_files=all_files,
            task_id=task.id
        )

        # Dynamic Plan Generation
        plan = DynamicPlanner.create_plan(
            task_id=task.id,
            requirement=f"{task.title}\n{task.description}",
            understanding=understanding,
            scanner=scanner
        )

        # Save Plan Steps to Database
        self.db.query(PlanStep).filter(PlanStep.task_id == task.id).delete()
        for step in plan.proposed_modifications:
            db_step = PlanStep(
                task_id=task.id,
                step_order=step.step_order,
                title=step.title,
                description=step.description,
                target_files=step.target_files,
                risk_level=step.risk_level,
                status="PENDING"
            )
            self.db.add(db_step)

        # Gate #1: Human Plan Approval
        self.db.query(ApprovalGate).filter(
            ApprovalGate.task_id == task.id,
            ApprovalGate.gate_type == GateType.PLAN.value
        ).delete()
        gate = ApprovalGate(
            task_id=task.id,
            gate_type=GateType.PLAN.value,
            proposed_payload=plan.model_dump(),
            status=ApprovalStatus.PENDING.value
        )
        self.db.add(gate)

        task.status = TaskStatus.AWAITING_PLAN_APPROVAL.value
        task.current_phase = "AWAITING_HUMAN_APPROVAL"
        self.db.commit()
        self.db.refresh(task)
        return plan

    # 3. Role: Coding Agent (Privileged Gate)
    def run_coding(self, task_id: str) -> List[PatchDiff]:
        task, workspace = self._get_task_and_workspace(task_id)

        # Privilege Check: Gate #1 MUST be APPROVED
        gate = self.db.query(ApprovalGate).filter(
            ApprovalGate.task_id == task.id,
            ApprovalGate.gate_type == GateType.PLAN.value,
            ApprovalGate.status == ApprovalStatus.APPROVED.value
        ).first()
        if not gate:
            raise SecurityException("Privileged operation denied: Plan must be approved before coding execution.")

        task.status = TaskStatus.CODING.value
        task.current_phase = "CODING_IN_ISOLATION"
        self.db.commit()

        # 1. Create isolated workspace
        if not task.isolated_workspace_path or not Path(task.isolated_workspace_path).exists():
            isolator = WorkspaceIsolator()
            isolated_path = isolator.create_isolated_copy(task.id, Path(workspace.path))
            task.isolated_workspace_path = str(isolated_path)
            self.db.commit()

        iso_dir = Path(task.isolated_workspace_path)
        scanner = RepositoryScanner(iso_dir)

        # 2. Generate and apply patches
        created_diffs: List[PatchDiff] = []
        try:
            # Check if real LLM is configured
            if hasattr(self.adapter, "model") and getattr(self.adapter, "model"):
                context = scanner.retrieve_context(f"{task.title}\n{task.description}", max_tokens=6000)
                context_payload = [{"path": f.relative_path, "content": f.content} for f in context]
                coding_output = self.adapter.generate_patch(
                    requirement=f"{task.title}\n{task.description}",
                    plan_step={"title": task.title, "description": task.description},
                    context_files=context_payload
                )
                patches = coding_output.patches
            else:
                # Controlled reference patches if present in memory or task
                patches = []

            for p in patches:
                orig, patched, diff_text = PatchEngine.apply_patch(iso_dir, p)
                diff_record = PatchDiff(
                    task_id=task.id,
                    file_path=p.file_path,
                    original_content=orig,
                    patched_content=patched,
                    diff_text=diff_text,
                    status="APPLIED_ISOLATED"
                )
                self.db.add(diff_record)
                created_diffs.append(diff_record)

            self.db.commit()
            return created_diffs

        except LLMConfigurationError as err:
            logger.info(f"Coding Agent: Model unconfigured ({err}) - holding in isolated state.")
            return []

    # 4. Role: Testing Agent
    def run_testing(self, task_id: str) -> ExecutionRun:
        task, workspace = self._get_task_and_workspace(task_id)
        if not task.isolated_workspace_path or not Path(task.isolated_workspace_path).exists():
            raise HTTPException(status_code=400, detail="No isolated workspace exists for testing")

        task.status = TaskStatus.VERIFYING.value
        task.current_phase = "RUNNING_SANDBOXED_TESTS"
        self.db.commit()

        runner = TestRunner(Path(task.isolated_workspace_path))
        cmd = runner.discover_test_command()
        exit_code, stdout, stderr, duration_ms = runner.execute_command(cmd)

        exec_run = ExecutionRun(
            task_id=task.id,
            command=" ".join(cmd),
            exit_code=exit_code,
            stdout=stdout,
            stderr=stderr,
            duration_ms=duration_ms,
            status="SUCCESS" if exit_code == 0 else "FAILED",
            phase="VERIFYING"
        )
        self.db.add(exec_run)
        self.db.commit()
        return exec_run

    # 5. Role: Debugging Agent
    def run_debugging(self, task_id: str, max_iterations: int = 3) -> Dict[str, Any]:
        task, workspace = self._get_task_and_workspace(task_id)
        if not task.isolated_workspace_path:
            raise HTTPException(status_code=400, detail="Isolated workspace required for debugging")

        agent = SelfDebuggingAgent(self.db, adapter=self.adapter, max_iterations=max_iterations)
        success = agent.run_self_debugging_loop(task.id)
        return {"task_id": task.id, "repair_successful": success}

    # 6. Role: Code Review Agent
    def run_code_review(self, task_id: str) -> Dict[str, Any]:
        task, workspace = self._get_task_and_workspace(task_id)
        review_engine = ReviewEngine(self.db)
        report = review_engine.generate_quality_report(task.id)
        conflicts = review_engine.detect_conflicts(task.id)

        task.status = TaskStatus.AWAITING_DIFF_APPROVAL.value
        task.current_phase = "AWAITING_DEVELOPER_DIFF_APPROVAL"
        self.db.commit()

        return {
            "quality_report": report.model_dump(),
            "conflicts": conflicts.model_dump()
        }
