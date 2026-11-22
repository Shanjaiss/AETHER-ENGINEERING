from typing import List, Optional
from pathlib import Path
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.models.workspace import Workspace
from backend.app.models.task import Task, TaskStatus
from backend.app.schemas.task import TaskCreate, TaskResponse
from backend.app.schemas.task_understanding import TaskUnderstandingResult
from backend.app.services.task_understanding.task_analyzer import TaskUnderstandingEngine
from backend.app.services.repo_intelligence.scanner import RepositoryScanner

router = APIRouter()

class RequirementAnalysisRequest(BaseModel):
    title: str
    description: str
    workspace_id: Optional[str] = None

@router.post("/analyze-requirement", response_model=TaskUnderstandingResult, summary="Analyze requirement intent, ambiguity and risk before execution")
def analyze_requirement(req: RequirementAnalysisRequest, db: Session = Depends(get_db)):
    repo_files = []
    if req.workspace_id:
        ws = db.query(Workspace).filter(Workspace.id == req.workspace_id).first()
        if ws and Path(ws.path).exists():
            try:
                scanner = RepositoryScanner(Path(ws.path))
                repo_files = scanner.list_repo_files()
            except Exception:
                pass

    return TaskUnderstandingEngine.analyze(
        title=req.title,
        description=req.description,
        repo_files=repo_files
    )

@router.post("/{task_id}/analyze", response_model=TaskUnderstandingResult, summary="Perform full understanding analysis on an existing task")
def analyze_task(task_id: str, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    repo_files = []
    ws = db.query(Workspace).filter(Workspace.id == task.workspace_id).first()
    if ws and Path(ws.path).exists():
        try:
            scanner = RepositoryScanner(Path(ws.path))
            repo_files = scanner.list_repo_files()
        except Exception:
            pass

    return TaskUnderstandingEngine.analyze(
        title=task.title,
        description=task.description,
        repo_files=repo_files,
        task_id=task.id
    )

@router.get("/", response_model=List[TaskResponse], summary="List engineering tasks")
def list_tasks(
    workspace_id: Optional[str] = Query(None, description="Filter by workspace ID"),
    db: Session = Depends(get_db)
):
    query = db.query(Task)
    if workspace_id:
        query = query.filter(Task.workspace_id == workspace_id)
    return query.order_by(Task.created_at.desc()).all()

@router.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED, summary="Create a new engineering task")
def create_task(task_in: TaskCreate, db: Session = Depends(get_db)):
    workspace = db.query(Workspace).filter(Workspace.id == task_in.workspace_id).first()
    if not workspace:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")

    task = Task(
        workspace_id=task_in.workspace_id,
        title=task_in.title,
        description=task_in.description,
        status=TaskStatus.PENDING.value,
        current_phase="INITIALIZATION"
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task

@router.get("/{task_id}", response_model=TaskResponse, summary="Get task details")
def get_task(task_id: str, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return task

@router.post("/{task_id}/cancel", response_model=TaskResponse, summary="Cancel an active task")
def cancel_task(task_id: str, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    task.status = TaskStatus.CANCELLED.value
    task.current_phase = "CANCELLED"
    db.commit()
    db.refresh(task)
    return task

