from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.schemas.task import TaskResponse, ExecutionRunResponse
from backend.app.models.task import ExecutionRun
from backend.app.services.debugging.self_debugging_agent import SelfDebuggingAgent

router = APIRouter()

@router.post("/{task_id}/run", response_model=TaskResponse, summary="Run test verification and self-debugging loop")
def run_verification(task_id: str, db: Session = Depends(get_db)):
    agent = SelfDebuggingAgent(db=db)
    return agent.verify_and_repair(task_id=task_id)

@router.get("/{task_id}/executions", response_model=List[ExecutionRunResponse], summary="Get execution runs for task")
def get_executions(task_id: str, db: Session = Depends(get_db)):
    return db.query(ExecutionRun).filter(ExecutionRun.task_id == task_id).order_by(ExecutionRun.created_at.asc()).all()

