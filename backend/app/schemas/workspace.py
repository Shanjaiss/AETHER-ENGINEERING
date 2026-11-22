import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, ConfigDict, Field

class WorkspaceBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    path: str = Field(..., description="Absolute path to repository or project root")
    metadata_json: Optional[Dict[str, Any]] = Field(default_factory=dict)

class WorkspaceCreate(WorkspaceBase):
    pass

class RepositoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    workspace_id: str
    name: str
    path: str
    is_git: bool
    default_branch: str
    languages: Dict[str, Any]
    frameworks: List[str]
    file_count: str
    created_at: datetime.datetime

class WorkspaceResponse(WorkspaceBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    is_active: bool
    created_at: datetime.datetime
    updated_at: datetime.datetime
    repositories: List[RepositoryResponse] = Field(default_factory=list)

