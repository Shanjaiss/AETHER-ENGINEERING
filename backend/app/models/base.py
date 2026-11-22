import datetime
from sqlalchemy import Column, DateTime
from backend.app.core.database import Base

def utc_now():
    return datetime.datetime.now(datetime.timezone.utc)

class TimestampMixin:
    """Standard timestamp mixin for database models."""
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        nullable=False
    )
