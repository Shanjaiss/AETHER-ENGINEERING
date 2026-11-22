from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

class HealthResponse(BaseModel):
    status: str = Field(..., json_schema_extra={"example": "healthy"})
    version: str = Field(..., json_schema_extra={"example": "1.0.0-rc.1"})
    environment: str = Field(..., json_schema_extra={"example": "development"})
    database_connected: bool = True
    llm_configured: bool = False
    llm_provider: str = "unconfigured"
    details: Dict[str, Any] = Field(default_factory=dict)
