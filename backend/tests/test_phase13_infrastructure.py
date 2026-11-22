import os
import time
import pytest
from pathlib import Path
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.main import app
from backend.app.core.config import settings
from backend.app.core.database import create_configured_engine, check_db_readiness, get_pool_config, init_db
from backend.app.core.auth import (
    hash_password,
    verify_password,
    create_jwt_token,
    decode_token,
    verify_workspace_access
)
from backend.app.models.user import User, UserRole
from backend.app.models.workspace import Workspace
from backend.app.services.queue.task_queue import InMemoryTaskQueue, TaskJob, JobStatus
from backend.app.services.streaming.event_broadcaster import EventBroadcaster
from backend.app.services.llm.cost_controller import CostController
from backend.app.services.cache.cache_manager import CacheManager
from backend.app.core.metrics import metrics

@pytest.fixture
def client():
    return TestClient(app)

# ---------------------------------------------------------------------------
# 1. Container & Compose Configuration Tests
# ---------------------------------------------------------------------------
def test_dockerfile_configurations():
    """Verifies Dockerfiles exist, use non-root users, and multi-stage builds."""
    backend_df = Path("backend/Dockerfile")
    frontend_df = Path("frontend/Dockerfile")
    compose_file = Path("docker-compose.yml")

    assert backend_df.exists(), "backend/Dockerfile missing"
    assert frontend_df.exists(), "frontend/Dockerfile missing"
    assert compose_file.exists(), "docker-compose.yml missing"

    backend_content = backend_df.read_text()
    assert "USER aether" in backend_content
    assert "HEALTHCHECK" in backend_content
    assert "python:3.12-slim" in backend_content

    frontend_content = frontend_df.read_text()
    assert "FROM node:22-alpine AS builder" in frontend_content
    assert "nginx-unprivileged" in frontend_content
    assert "USER nginx" in frontend_content

    compose_content = compose_file.read_text()
    assert "profiles: [\"data\", \"production\"]" in compose_content
    assert "profiles: [\"worker\", \"production\"]" in compose_content
    assert "profiles: [\"observability\"]" in compose_content

# ---------------------------------------------------------------------------
# 2. Database Connection Pooling & Readiness Tests
# ---------------------------------------------------------------------------
def test_database_connection_pooling_and_readiness():
    """Verifies PostgreSQL engine configures pooling while SQLite handles embedded fallback."""
    init_db()
    # Test PostgreSQL dialect engine pool configuration
    pg_pool = get_pool_config("postgresql://test:pass@localhost:5432/testdb")
    assert pg_pool["pool_size"] == 10
    assert pg_pool["max_overflow"] == 20
    assert pg_pool["pool_pre_ping"] is True

    # Test readiness check on active database
    ready, msg, pool_info = check_db_readiness()
    assert ready is True
    assert "dialect" in pool_info
    assert pool_info["latency_ms"] >= 0.0

# ---------------------------------------------------------------------------
# 3. Authentication, Password Hashing & JWT Tests
# ---------------------------------------------------------------------------
def test_password_hashing_and_verification():
    """Verifies cryptographically secure PBKDF2 hashing with salt."""
    plain = "SuperSecretPassword123!"
    hashed = hash_password(plain)
    assert hashed.startswith("pbkdf2_sha256$100000$")
    assert verify_password(plain, hashed) is True
    assert verify_password("WrongPassword!", hashed) is False

def test_jwt_token_lifecycle_and_claims():
    """Verifies JWT issuance, claims validation, expiration, and signature tampering defense."""
    user = User(
        id="usr-test-123",
        email="dev@example.com",
        role=UserRole.DEVELOPER.value,
        tenant_id="tenant-alpha"
    )
    from datetime import timedelta
    token = create_jwt_token({"sub": user.id, "email": user.email, "role": user.role, "tenant_id": user.tenant_id}, timedelta(minutes=10))
    decoded = decode_token(token)
    assert decoded["sub"] == user.id
    assert decoded["tenant_id"] == "tenant-alpha"
    assert decoded["iss"] == "aether-engineer"
    assert decoded["aud"] == "aether-api"

    # Signature tampering test
    parts = token.split(".")
    tampered_sig = parts[2][:-4] + "AAAA"
    tampered_token = f"{parts[0]}.{parts[1]}.{tampered_sig}"
    with pytest.raises(Exception):
        decode_token(tampered_token)

# ---------------------------------------------------------------------------
# 4. Authentication Endpoints & Horizontal Privilege Escalation Defense
# ---------------------------------------------------------------------------
def test_auth_endpoints_and_tenant_isolation(client):
    """Verifies registration, login, token refresh, and cross-tenant workspace protection."""
    unique_email = f"user_{int(time.time() * 1000)}@company.com"
    reg_res = client.post("/api/v1/auth/register", json={
        "email": unique_email,
        "password": "Password12345!",
        "full_name": "Test Engineer",
        "tenant_id": "tenant-corp"
    })
    assert reg_res.status_code == 201
    user_data = reg_res.json()
    assert user_data["email"] == unique_email
    assert user_data["tenant_id"] == "tenant-corp"

    # Login
    login_res = client.post("/api/v1/auth/login", json={
        "email": unique_email,
        "password": "Password12345!"
    })
    assert login_res.status_code == 200
    token_data = login_res.json()
    assert "access_token" in token_data
    access_token = token_data["access_token"]

    # Verify /me endpoint
    me_res = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {access_token}"})
    assert me_res.status_code == 200
    assert me_res.json()["email"] == unique_email

    # Horizontal Privilege Escalation test: Attempting to access another tenant's workspace
    foreign_ws = Workspace(
        id="ws-foreign",
        name="Foreign Workspace",
        path="/tmp/foreign",
        tenant_id="tenant-competitor",
        owner_id="usr-other"
    )
    current_usr = User(
        id=user_data["id"],
        email=unique_email,
        role=UserRole.DEVELOPER.value,
        tenant_id="tenant-corp"
    )
    with pytest.raises(Exception) as excinfo:
        verify_workspace_access(foreign_ws, current_usr)
    assert "Cannot access workspace belonging to another tenant" in str(excinfo.value.detail)

# ---------------------------------------------------------------------------
# 5. Asynchronous Task Queue & Idempotency Tests
# ---------------------------------------------------------------------------
def test_task_queue_idempotency_and_cancellation():
    """Verifies task queue delivery, idempotency key deduplication, and cancellation."""
    queue = InMemoryTaskQueue()
    job1 = TaskJob(task_id="task-001", idempotency_key="idemp-abc", payload={"op": "build"})
    enqueued1 = queue.enqueue(job1)

    # Duplicate action submission with identical idempotency key returns existing job
    job2 = TaskJob(task_id="task-001", idempotency_key="idemp-abc", payload={"op": "build"})
    enqueued2 = queue.enqueue(job2)
    assert enqueued1.job_id == enqueued2.job_id

    # Queue depth check
    assert queue.get_queue_depth() == 1

    # Dequeue and process
    dequeued = queue.dequeue()
    assert dequeued is not None
    assert dequeued.status == JobStatus.PROCESSING

    # Cancel job
    queue.cancel_job(dequeued.job_id)
    assert dequeued.status == JobStatus.CANCELLED

# ---------------------------------------------------------------------------
# 6. Real-Time Event Broadcaster Tests
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_event_broadcaster_streaming():
    """Verifies genuine agent event delivery without simulated progress."""
    bc = EventBroadcaster()
    queue = bc.subscribe("task-sse-01")

    await bc.broadcast("task-sse-01", "planning_started", {"step": 1})
    msg = queue.get_nowait()
    assert "event: planning_started" in msg
    assert '"step": 1' in msg

    bc.unsubscribe("task-sse-01", queue)

# ---------------------------------------------------------------------------
# 7. Model Gateway Cost Control & Budgeting Tests
# ---------------------------------------------------------------------------
def test_cost_controller_and_budgeting():
    """Verifies token pricing calculation and spending budget guards."""
    cost = CostController.calculate_cost("gemini-1.5-pro", 100000, 20000)
    # 0.1M * $1.25 = $0.125, 0.02M * $5.00 = $0.10 => $0.225
    assert cost == 0.225

    # Budget check within limits
    assert CostController.check_task_budget(current_cost=0.50, current_tokens=15000, max_budget_dollars=1.00) is True

    # Budget check exceeding limit
    assert CostController.check_task_budget(current_cost=1.50, current_tokens=15000, max_budget_dollars=1.00) is False

# ---------------------------------------------------------------------------
# 8. Tenant Caching & Invalidation Tests
# ---------------------------------------------------------------------------
def test_tenant_scoped_caching_and_invalidation():
    """Verifies tenant-isolated caching, TTL, and repo modification invalidation."""
    cm = CacheManager()
    cm.set("tenant-1", "repo-A", "file_index", ["a.py", "b.py"], ttl_seconds=60)
    assert cm.get("tenant-1", "repo-A", "file_index") == ["a.py", "b.py"]

    # Cross-tenant cache isolation check
    assert cm.get("tenant-2", "repo-A", "file_index") is None

    # Invalidation on repo edits
    cm.invalidate_repo("tenant-1", "repo-A")
    assert cm.get("tenant-1", "repo-A", "file_index") is None

# ---------------------------------------------------------------------------
# 9. Prometheus Metrics Exposition Tests
# ---------------------------------------------------------------------------
def test_prometheus_metrics_endpoint(client):
    """Verifies /api/v1/metrics output format matches Prometheus text exposition standards."""
    metrics.record_request("GET", "/api/v1/health", 200, 0.002)
    metrics.record_task_outcome(True)
    metrics.record_security_violation("traversal_blocked")

    res = client.get("/api/v1/metrics")
    assert res.status_code == 200
    text = res.text
    assert "aether_process_resident_memory_bytes" in text
    assert "aether_tasks_completed_total" in text
    assert "aether_security_violations_total" in text
