import uuid
import enum
from sqlalchemy import Column, String, Boolean
from backend.app.core.database import Base
from backend.app.models.base import TimestampMixin

class UserRole(str, enum.Enum):
    ADMIN = "ADMIN"
    DEVELOPER = "DEVELOPER"
    VIEWER = "VIEWER"

class User(Base, TimestampMixin):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    role = Column(String, default=UserRole.DEVELOPER.value)
    tenant_id = Column(String, index=True, default="default-tenant", nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

