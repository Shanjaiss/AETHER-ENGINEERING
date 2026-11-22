import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, ConfigDict, Field

class PlanStepBase(BaseModel):
    step_order: int
    title: str
    description: str
    target_files: List[str] = Field(default_factory=list)
    risk_level: str = "LOW"

class PlanStepResponse(PlanStepBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    task_id: str
    status: str
    created_at: datetime.datetime

class ApprovalGateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    task_id: str
    gate_type: str
    proposed_payload: Dict[str, Any]
    status: str
    decision_notes: Optional[str]
    decided_at: Optional[datetime.datetime]
    created_at: datetime.datetime

class ApprovalDecisionRequest(BaseModel):
    decision: str = Field(..., pattern="^(APPROVED|REJECTED)$")
    notes: Optional[str] = None

class PatchDiffResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    task_id: str
    file_path: str
    original_content: Optional[str]
    patched_content: Optional[str]
    diff_text: str
    status: str
    created_at: datetime.datetime

class ExecutionRunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    task_id: str
    phase: str
    command: str
    stdout: str
    stderr: str
    exit_code: int
    duration_ms: int
    status: str
    created_at: datetime.datetime

class TaskCreate(BaseModel):
    workspace_id: str
    title: str = Field(..., min_length=3, max_length=200)
    description: str = Field(..., min_length=5)

class TaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    workspace_id: str
    title: str
    description: str
    status: str
    current_phase: str
    model_used: Optional[str]
    isolated_workspace_path: Optional[str]
    repair_attempts: int
    error_summary: Optional[str]
    created_at: datetime.datetime
    updated_at: datetime.datetime
    plan_steps: List[PlanStepResponse] = Field(default_factory=list)
    approvals: List[ApprovalGateResponse] = Field(default_factory=list)
    patches: List[PatchDiffResponse] = Field(default_factory=list)
    executions: List[ExecutionRunResponse] = Field(default_factory=list)

