from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.schemas.task import TaskResponse, ApprovalDecisionRequest
from backend.app.services.orchestrator.planning_agent import PlanningAgent

router = APIRouter()

@router.post("/{task_id}/generate", response_model=TaskResponse, summary="Generate structured engineering plan")
def generate_plan(task_id: str, db: Session = Depends(get_db)):
    agent = PlanningAgent(db=db)
    return agent.generate_plan(task_id=task_id)

@router.post("/{task_id}/approve", response_model=TaskResponse, summary="Submit human approval or rejection of plan")
def approve_plan(task_id: str, payload: ApprovalDecisionRequest, db: Session = Depends(get_db)):
    agent = PlanningAgent(db=db)
    return agent.submit_approval(task_id=task_id, decision=payload.decision, notes=payload.notes)

