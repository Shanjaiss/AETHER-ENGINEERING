import uuid
import datetime
from sqlalchemy import Column, String, Integer, Float, Text, Boolean, JSON, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
import enum
from backend.app.core.database import Base
from backend.app.models.base import TimestampMixin, utc_now

class TaskStatus(str, enum.Enum):
    PENDING = "PENDING"
    ANALYZING = "ANALYZING"
    PLANNING = "PLANNING"
    AWAITING_PLAN_APPROVAL = "AWAITING_PLAN_APPROVAL"
    CODING = "CODING"
    VERIFYING = "VERIFYING"
    DEBUGGING = "DEBUGGING"
    AWAITING_DIFF_APPROVAL = "AWAITING_DIFF_APPROVAL"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"

class ApprovalStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"

class GateType(str, enum.Enum):
    PLAN = "PLAN"
    DIFF = "DIFF"
    COMMAND = "COMMAND"

class Task(Base, TimestampMixin):
    __tablename__ = "tasks"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String, index=True, default="default-tenant", nullable=False)
    created_by_user_id = Column(String, nullable=True, index=True)
    workspace_id = Column(String, ForeignKey("workspaces.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    status = Column(String, default=TaskStatus.PENDING.value)
    current_phase = Column(String, default="INITIALIZATION")
    model_used = Column(String, nullable=True)
    isolated_workspace_path = Column(String, nullable=True)
    repair_attempts = Column(Integer, default=0)
    error_summary = Column(Text, nullable=True)

    workspace = relationship("Workspace", back_populates="tasks")
    plan_steps = relationship("PlanStep", back_populates="task", cascade="all, delete-orphan", order_by="PlanStep.step_order")
    executions = relationship("ExecutionRun", back_populates="task", cascade="all, delete-orphan")
    approvals = relationship("ApprovalGate", back_populates="task", cascade="all, delete-orphan")
    patches = relationship("PatchDiff", back_populates="task", cascade="all, delete-orphan")

class PlanStep(Base, TimestampMixin):
    __tablename__ = "plan_steps"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    task_id = Column(String, ForeignKey("tasks.id"), nullable=False)
    step_order = Column(Integer, nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    target_files = Column(JSON, default=list)
    risk_level = Column(String, default="LOW")  # LOW, MEDIUM, HIGH
    status = Column(String, default="PENDING")

    task = relationship("Task", back_populates="plan_steps")

class ExecutionRun(Base):
    __tablename__ = "execution_runs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    task_id = Column(String, ForeignKey("tasks.id"), nullable=False)
    phase = Column(String, nullable=False)
    command = Column(String, nullable=False)
    stdout = Column(Text, default="")
    stderr = Column(Text, default="")
    exit_code = Column(Integer, nullable=False)
    duration_ms = Column(Integer, default=0)
    status = Column(String, nullable=False)  # SUCCESS, FAILURE, TIMEOUT, ERROR
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    task = relationship("Task", back_populates="executions")

class ApprovalGate(Base, TimestampMixin):
    __tablename__ = "approval_gates"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    task_id = Column(String, ForeignKey("tasks.id"), nullable=False)
    gate_type = Column(String, default=GateType.PLAN.value)
    proposed_payload = Column(JSON, default=dict)
    status = Column(String, default=ApprovalStatus.PENDING.value)
    decision_notes = Column(Text, nullable=True)
    decided_at = Column(DateTime, nullable=True)

    task = relationship("Task", back_populates="approvals")

class PatchDiff(Base, TimestampMixin):
    __tablename__ = "patch_diffs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    task_id = Column(String, ForeignKey("tasks.id"), nullable=False)
    file_path = Column(String, nullable=False)
    original_content = Column(Text, nullable=True)
    patched_content = Column(Text, nullable=True)
    diff_text = Column(Text, nullable=False)
    status = Column(String, default="PROPOSED")  # PROPOSED, APPLIED, REVERTED, MERGED

    task = relationship("Task", back_populates="patches")

class BenchmarkRun(Base):
    __tablename__ = "benchmark_runs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    benchmark_id = Column(String, nullable=False)
    name = Column(String, nullable=False)
    category = Column(String, nullable=False)
    model_name = Column(String, nullable=False)
    test_passed = Column(Boolean, default=False)
    duration_seconds = Column(Float, default=0.0)
    repair_attempts = Column(Integer, default=0)
    token_usage = Column(JSON, default=dict)
    details = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
