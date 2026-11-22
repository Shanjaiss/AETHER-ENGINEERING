import uuid
import datetime
from sqlalchemy import Column, String, JSON, DateTime
from backend.app.core.database import Base
from backend.app.models.base import utc_now

class AuditEvent(Base):
    __tablename__ = "audit_events"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String, index=True, nullable=False, default="default-tenant")
    user_id = Column(String, index=True, nullable=True)
    event_type = Column(String, nullable=False, index=True)
    resource_type = Column(String, nullable=True)
    resource_id = Column(String, nullable=True)
    status = Column(String, default="SUCCESS")
    details = Column(JSON, default=dict)
    ip_address = Column(String, nullable=True)
    timestamp = Column(DateTime, default=utc_now, nullable=False, index=True)

