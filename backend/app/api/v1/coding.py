from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.schemas.task import TaskResponse, PatchDiffResponse
from backend.app.models.task import PatchDiff
from backend.app.services.coding_engine.coding_agent import CodingAgent

router = APIRouter()

@router.post("/{task_id}/execute", response_model=TaskResponse, summary="Execute code patches in isolated sandbox")
def execute_coding(task_id: str, db: Session = Depends(get_db)):
    agent = CodingAgent(db=db)
    return agent.execute_coding(task_id=task_id)

@router.post("/{task_id}/rollback", response_model=TaskResponse, summary="Rollback isolated workspace to original state")
def rollback_coding(task_id: str, db: Session = Depends(get_db)):
    agent = CodingAgent(db=db)
    return agent.rollback(task_id=task_id)

@router.get("/{task_id}/diffs", response_model=List[PatchDiffResponse], summary="Get generated diffs for task")
def get_diffs(task_id: str, db: Session = Depends(get_db)):
    return db.query(PatchDiff).filter(PatchDiff.task_id == task_id).all()

