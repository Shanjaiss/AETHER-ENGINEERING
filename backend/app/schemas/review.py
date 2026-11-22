from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class ChangedFileMetric(BaseModel):
    file_path: str
    lines_added: int
    lines_removed: int
    risk_level: str

class QualityReportResponse(BaseModel):
    task_id: str
    total_files_changed: int
    total_lines_added: int
    total_lines_removed: int
    overall_risk: str  # LOW | MEDIUM | HIGH
    security_warnings: List[str]
    static_analysis_passed: bool
    test_evidence: Dict[str, Any]
    changed_files: List[ChangedFileMetric]
    summary: str

class ConflictCheckResponse(BaseModel):
    has_conflicts: bool
    conflicted_files: List[str]
    message: str

class ReviewDecisionRequest(BaseModel):
    decision: str = Field(..., pattern="^(APPROVED|REJECTED)$")
    notes: Optional[str] = None

