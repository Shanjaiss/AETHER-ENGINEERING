from typing import Optional
from pydantic import BaseModel, Field

class UserRegisterRequest(BaseModel):
    email: str = Field(..., description="User email address")
    password: str = Field(..., min_length=8, description="Minimum 8-character password")
    full_name: Optional[str] = None
    role: Optional[str] = "DEVELOPER"
    tenant_id: Optional[str] = "default-tenant"

class UserLoginRequest(BaseModel):
    email: str
    password: str

class TokenRefreshRequest(BaseModel):
    refresh_token: str

class UserResponse(BaseModel):
    id: str
    email: str
    full_name: Optional[str] = None
    role: str
    tenant_id: str
    is_active: bool
    created_at: Optional[str] = None

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse

