from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pathlib import Path

from backend.app.core.database import get_db
from backend.app.core.security import validate_safe_path
from backend.app.models.workspace import Workspace
from backend.app.schemas.workspace import WorkspaceCreate, WorkspaceResponse

router = APIRouter()

@router.get("/", response_model=List[WorkspaceResponse], summary="List all workspaces")
def list_workspaces(db: Session = Depends(get_db)):
    return db.query(Workspace).order_by(Workspace.created_at.desc()).all()

@router.post("/", response_model=WorkspaceResponse, status_code=status.HTTP_201_CREATED, summary="Create or register workspace")
def create_workspace(workspace_in: WorkspaceCreate, db: Session = Depends(get_db)):
    # Validate that path is safe and canonical
    safe_path = validate_safe_path(workspace_in.path)
    
    # Check if already registered
    existing = db.query(Workspace).filter(Workspace.path == str(safe_path)).first()
    if existing:
        return existing

    workspace = Workspace(
        name=workspace_in.name,
        path=str(safe_path),
        is_active=True,
        metadata_json=workspace_in.metadata_json or {}
    )
    db.add(workspace)
    db.commit()
    db.refresh(workspace)
    return workspace

@router.get("/{workspace_id}", response_model=WorkspaceResponse, summary="Get workspace details")
def get_workspace(workspace_id: str, db: Session = Depends(get_db)):
    workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    if not workspace:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")
    return workspace

@router.delete("/{workspace_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete workspace")
def delete_workspace(workspace_id: str, db: Session = Depends(get_db)):
    workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    if not workspace:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")
    db.delete(workspace)
    db.commit()
    return None

