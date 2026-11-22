from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.schemas.task import TaskResponse
from backend.app.schemas.review import (
    QualityReportResponse,
    ConflictCheckResponse,
    ReviewDecisionRequest
)
from backend.app.services.review.review_engine import ReviewEngine

router = APIRouter()

@router.get("/{task_id}/report", response_model=QualityReportResponse, summary="Get engineering quality and security report")
def get_quality_report(task_id: str, db: Session = Depends(get_db)):
    engine = ReviewEngine(db=db)
    return engine.generate_quality_report(task_id=task_id)

@router.get("/{task_id}/conflicts", response_model=ConflictCheckResponse, summary="Check for conflicts with original repo")
def check_conflicts(task_id: str, db: Session = Depends(get_db)):
    engine = ReviewEngine(db=db)
    return engine.detect_conflicts(task_id=task_id)

@router.get("/{task_id}/export", summary="Export unified git patch")
def export_patch(task_id: str, db: Session = Depends(get_db)):
    engine = ReviewEngine(db=db)
    patch_text = engine.export_patch(task_id=task_id)
    return Response(
        content=patch_text,
        media_type="text/x-diff",
        headers={"Content-Disposition": f"attachment; filename=task_{task_id}.patch"}
    )

@router.post("/{task_id}/decision", response_model=TaskResponse, summary="Submit developer approval or rejection")
def submit_decision(task_id: str, payload: ReviewDecisionRequest, db: Session = Depends(get_db)):
    engine = ReviewEngine(db=db)
    return engine.submit_review_decision(task_id=task_id, decision=payload.decision, notes=payload.notes)

@router.post("/{task_id}/apply", response_model=TaskResponse, summary="Safely apply approved changes to original repository")
def apply_changes(task_id: str, db: Session = Depends(get_db)):
    engine = ReviewEngine(db=db)
    return engine.apply_approved_patches(task_id=task_id)

