import os
import time
import json
import hmac
import hashlib
import base64
import secrets
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone, timedelta
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.core.database import get_db
from backend.app.models.user import User, UserRole
from backend.app.models.audit import AuditEvent
from backend.app.models.workspace import Workspace

# Secret key for signing tokens
JWT_SECRET = os.environ.get("AETHER_JWT_SECRET", "aether-secure-production-jwt-secret-key-m1-mac-8gb")
JWT_ALGORITHM = "HS256"
JWT_ISSUER = "aether-engineer"
JWT_AUDIENCE = "aether-api"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
REFRESH_TOKEN_EXPIRE_DAYS = 7

http_bearer_scheme = HTTPBearer(auto_error=False)

def b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode('utf-8')

def b64url_decode(data_str: str) -> bytes:
    padding = '=' * (4 - (len(data_str) % 4)) if len(data_str) % 4 != 0 else ''
    return base64.urlsafe_b64decode((data_str + padding).encode('utf-8'))

def hash_password(password: str) -> str:
    """Hashes password using PBKDF2-HMAC-SHA256 with a unique random salt."""
    salt = secrets.token_hex(16)
    key = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt.encode('utf-8'),
        iterations=100000
    )
    return f"pbkdf2_sha256$100000${salt}${key.hex()}"

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies plain password against PBKDF2 hash with constant-time comparison."""
    try:
        algo, iters, salt, stored_key = hashed_password.split('$')
        iterations = int(iters)
        calculated_key = hashlib.pbkdf2_hmac(
            'sha256',
            plain_password.encode('utf-8'),
            salt.encode('utf-8'),
            iterations=iterations
        ).hex()
        return hmac.compare_digest(calculated_key, stored_key)
    except Exception:
        return False

def create_jwt_token(payload: Dict[str, Any], expires_delta: timedelta) -> str:
    """Creates a signed HMAC-SHA256 JWT token with standard claims."""
    now = datetime.now(timezone.utc)
    exp = now + expires_delta
    claims = {
        **payload,
        "iss": JWT_ISSUER,
        "aud": JWT_AUDIENCE,
        "iat": int(now.timestamp()),
        "exp": int(exp.timestamp())
    }
    header = {"alg": JWT_ALGORITHM, "typ": "JWT"}
    header_b64 = b64url_encode(json.dumps(header, separators=(',', ':')).encode('utf-8'))
    payload_b64 = b64url_encode(json.dumps(claims, separators=(',', ':')).encode('utf-8'))
    signing_input = f"{header_b64}.{payload_b64}".encode('utf-8')
    signature = hmac.new(JWT_SECRET.encode('utf-8'), signing_input, hashlib.sha256).digest()
    sig_b64 = b64url_encode(signature)
    return f"{header_b64}.{payload_b64}.{sig_b64}"

def create_access_token(user: User) -> str:
    payload = {
        "sub": user.id,
        "email": user.email,
        "role": user.role,
        "tenant_id": user.tenant_id,
        "token_type": "access"
    }
    return create_jwt_token(payload, timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))

def create_refresh_token(user: User) -> str:
    payload = {
        "sub": user.id,
        "tenant_id": user.tenant_id,
        "token_type": "refresh"
    }
    return create_jwt_token(payload, timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS))

def decode_token(token: str) -> Dict[str, Any]:
    """Decodes and verifies a JWT token. Raises HTTPException if invalid or expired."""
    try:
        parts = token.split('.')
        if len(parts) != 3:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token format")
        header_b64, payload_b64, sig_b64 = parts
        signing_input = f"{header_b64}.{payload_b64}".encode('utf-8')
        expected_sig = hmac.new(JWT_SECRET.encode('utf-8'), signing_input, hashlib.sha256).digest()
        provided_sig = b64url_decode(sig_b64)
        if not hmac.compare_digest(expected_sig, provided_sig):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token signature mismatch")

        payload = json.loads(b64url_decode(payload_b64).decode('utf-8'))

        # Verify claims
        now_ts = int(datetime.now(timezone.utc).timestamp())
        if payload.get("exp", 0) < now_ts:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired")
        if payload.get("iss") != JWT_ISSUER:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token issuer")
        if payload.get("aud") != JWT_AUDIENCE:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token audience")

        return payload
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Token verification error: {str(e)}")

def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(http_bearer_scheme),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """Dependency that returns the authenticated User or None if unauthenticated."""
    if not credentials or not credentials.credentials:
        return None
    token = credentials.credentials
    payload = decode_token(token)
    user_id = payload.get("sub")
    if not user_id:
        return None
    user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
    return user

def require_current_user(current_user: Optional[User] = Depends(get_current_user)) -> User:
    """Dependency requiring an authenticated active user."""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"}
        )
    return current_user

def require_role(allowed_roles: List[str]):
    """Role-based access control dependency factory."""
    def role_checker(current_user: User = Depends(require_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied: required role in {allowed_roles}, got {current_user.role}"
            )
        return current_user
    return role_checker

def verify_workspace_access(workspace: Workspace, current_user: Optional[User]) -> None:
    """Guards against cross-tenant and unauthorized cross-workspace access (Horizontal Privilege Escalation)."""
    if current_user is None:
        # In open local dev mode with no auth headers, allowed
        return
    # If user is ADMIN, allowed across tenant
    if current_user.role == UserRole.ADMIN.value:
        return
    # Enforce tenant isolation
    if workspace.tenant_id != current_user.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Cannot access workspace belonging to another tenant."
        )
    # If workspace has an explicit owner and current user is not owner
    if workspace.owner_id and workspace.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: You do not have ownership permissions for this workspace."
        )

def record_audit_event(
    db: Session,
    event_type: str,
    user_id: Optional[str] = None,
    tenant_id: str = "default-tenant",
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    status: str = "SUCCESS",
    details: Optional[Dict[str, Any]] = None,
    ip_address: Optional[str] = None
) -> AuditEvent:
    """Records an immutable security audit event."""
    event = AuditEvent(
        tenant_id=tenant_id,
        user_id=user_id,
        event_type=event_type,
        resource_type=resource_type,
        resource_id=resource_id,
        status=status,
        details=details or {},
        ip_address=ip_address
    )
    db.add(event)
    try:
        db.commit()
    except Exception:
        db.rollback()
    return event
