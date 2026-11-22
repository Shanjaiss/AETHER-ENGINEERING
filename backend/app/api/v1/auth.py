from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.models.user import User, UserRole
from backend.app.models.audit import AuditEvent
from backend.app.schemas.auth import (
    UserRegisterRequest,
    UserLoginRequest,
    TokenRefreshRequest,
    UserResponse,
    TokenResponse
)
from backend.app.core.auth import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
    get_current_user,
    require_current_user,
    require_role,
    record_audit_event,
    ACCESS_TOKEN_EXPIRE_MINUTES
)

router = APIRouter()

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(req: UserRegisterRequest, request: Request, db: Session = Depends(get_db)):
    """Registers a new user account with hashed password and tenant boundary."""
    existing = db.query(User).filter(User.email == req.email.lower().strip()).first()
    if existing:
        record_audit_event(
            db,
            event_type="AUTH_REGISTER_FAIL",
            tenant_id=req.tenant_id or "default-tenant",
            status="DENIED",
            details={"email": req.email, "reason": "Email already exists"},
            ip_address=request.client.host if request.client else None
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email address already exists."
        )

    user = User(
        email=req.email.lower().strip(),
        hashed_password=hash_password(req.password),
        full_name=req.full_name,
        role=req.role or UserRole.DEVELOPER.value,
        tenant_id=req.tenant_id or "default-tenant",
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    record_audit_event(
        db,
        event_type="AUTH_REGISTER_SUCCESS",
        user_id=user.id,
        tenant_id=user.tenant_id,
        status="SUCCESS",
        details={"email": user.email, "role": user.role},
        ip_address=request.client.host if request.client else None
    )

    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        tenant_id=user.tenant_id,
        is_active=user.is_active,
        created_at=user.created_at.isoformat() if user.created_at else None
    )

@router.post("/login", response_model=TokenResponse)
def login(req: UserLoginRequest, request: Request, db: Session = Depends(get_db)):
    """Authenticates user credentials and issues signed access and refresh JWTs."""
    user = db.query(User).filter(User.email == req.email.lower().strip()).first()
    if not user or not verify_password(req.password, user.hashed_password):
        record_audit_event(
            db,
            event_type="AUTH_LOGIN_FAIL",
            status="FAILED",
            details={"email": req.email, "reason": "Bad credentials"},
            ip_address=request.client.host if request.client else None
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"}
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated"
        )

    access_token = create_access_token(user)
    refresh_token = create_refresh_token(user)

    record_audit_event(
        db,
        event_type="AUTH_LOGIN_SUCCESS",
        user_id=user.id,
        tenant_id=user.tenant_id,
        status="SUCCESS",
        ip_address=request.client.host if request.client else None
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserResponse(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            tenant_id=user.tenant_id,
            is_active=user.is_active,
            created_at=user.created_at.isoformat() if user.created_at else None
        )
    )

@router.post("/refresh", response_model=TokenResponse)
def refresh_token(req: TokenRefreshRequest, db: Session = Depends(get_db)):
    """Refreshes an expired access token using a valid refresh token."""
    payload = decode_token(req.refresh_token)
    if payload.get("token_type") != "refresh":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token type, expected refresh")

    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")

    new_access = create_access_token(user)
    new_refresh = create_refresh_token(user)

    return TokenResponse(
        access_token=new_access,
        refresh_token=new_refresh,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserResponse(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            tenant_id=user.tenant_id,
            is_active=user.is_active,
            created_at=user.created_at.isoformat() if user.created_at else None
        )
    )

@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(require_current_user)):
    """Returns the profile of the currently authenticated user."""
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        role=current_user.role,
        tenant_id=current_user.tenant_id,
        is_active=current_user.is_active,
        created_at=current_user.created_at.isoformat() if current_user.created_at else None
    )

@router.post("/logout")
def logout(current_user: User = Depends(require_current_user), db: Session = Depends(get_db)):
    """Logs out user and records audit trail."""
    record_audit_event(
        db,
        event_type="AUTH_LOGOUT",
        user_id=current_user.id,
        tenant_id=current_user.tenant_id,
        status="SUCCESS"
    )
    return {"message": "Successfully logged out"}

@router.get("/audit-logs")
def get_audit_logs(
    limit: int = 50,
    current_user: User = Depends(require_role([UserRole.ADMIN.value])),
    db: Session = Depends(get_db)
):
    """Admin-only endpoint retrieving recent security audit events within the tenant."""
    events = (
        db.query(AuditEvent)
        .filter(AuditEvent.tenant_id == current_user.tenant_id)
        .order_by(AuditEvent.timestamp.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": e.id,
            "tenant_id": e.tenant_id,
            "user_id": e.user_id,
            "event_type": e.event_type,
            "resource_type": e.resource_type,
            "resource_id": e.resource_id,
            "status": e.status,
            "details": e.details,
            "timestamp": e.timestamp.isoformat() if e.timestamp else None
        }
        for e in events
    ]

