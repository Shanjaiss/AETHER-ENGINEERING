import uuid
from sqlalchemy import Column, String, Boolean, JSON, ForeignKey
from sqlalchemy.orm import relationship
from backend.app.core.database import Base
from backend.app.models.base import TimestampMixin

class Workspace(Base, TimestampMixin):
    __tablename__ = "workspaces"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    path = Column(String, nullable=False, unique=True)
    is_active = Column(Boolean, default=True)
    metadata_json = Column(JSON, default=dict)

    # Relationships
    repositories = relationship("Repository", back_populates="workspace", cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="workspace", cascade="all, delete-orphan")

class Repository(Base, TimestampMixin):
    __tablename__ = "repositories"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    workspace_id = Column(String, ForeignKey("workspaces.id"), nullable=False)
    name = Column(String, nullable=False)
    path = Column(String, nullable=False)
    is_git = Column(Boolean, default=False)
    default_branch = Column(String, default="main")
    languages = Column(JSON, default=dict)
    frameworks = Column(JSON, default=list)
    file_count = Column(String, default="0")

    workspace = relationship("Workspace", back_populates="repositories")

