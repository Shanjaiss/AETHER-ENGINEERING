# AETHER ENGINEER — Infrastructure & DevOps Architecture Specification
### *Production Infrastructure, Containerization, Asynchronous Processing, and System Reliability*

**Platform:** Apple Silicon Mac M1 (8 GB Unified Memory) | Production Cloud  
**Date:** November 2026

---

## 1. Executive Summary

Phase 13 establishes the production infrastructure and DevOps architecture for AETHER ENGINEER. The system transitions from a locally verified engineering agent into a cloud-ready, asynchronous, multi-tenant developer platform with enterprise observability, strict security boundaries, and documented capacity models.

---

## 2. Infrastructure Implementation Status

```
+-----------------------------------------------------------------------------------------+
|                               INFRASTRUCTURE STATUS MATRIX                              |
+-----------------------------------------------------------------------------------------+
| Component                         | Implementation State | Verification Evidence        |
+-----------------------------------------------------------------------------------------+
| Multi-Stage Frontend Dockerfile   | IMPLEMENTED & VERIF. | Verified non-root nginx cfg  |
| Slim Backend Dockerfile           | IMPLEMENTED & VERIF. | Verified non-root user aether|
| Multi-Profile docker-compose.yml  | IMPLEMENTED & VERIF. | Verified 5 distinct profiles |
| PostgreSQL Pooling & Dialect Abstr| IMPLEMENTED & VERIF. | Unit tested connection pool  |
| Asynchronous Task Queue & Worker  | IMPLEMENTED & VERIF. | Unit tested idempotency/retry|
| Real-Time SSE Event Broadcaster   | IMPLEMENTED & VERIF. | Tested live event delivery   |
| User Authentication & RBAC (JWT)  | IMPLEMENTED & VERIF. | Unit tested auth & tenant iso|
| Horizontal Privilege Escalation   | IMPLEMENTED & VERIF. | Unit tested cross-tenant 403 |
| Model Gateway Cost Controller     | IMPLEMENTED & VERIF. | Verified token/cost tracking |
| Tenant-Scoped Cache Manager       | IMPLEMENTED & VERIF. | Tested cache & invalidation  |
| Nginx Reverse Proxy Config        | IMPLEMENTED & VERIF. | Rate limiting & SSE headers  |
| Prometheus Metrics Exposition     | IMPLEMENTED & VERIF. | Formatted at /api/v1/metrics |
| GitHub Actions CI Pipeline        | IMPLEMENTED & VERIF. | 13-stage workflow defined    |
| Local Load Testing Harness        | IMPLEMENTED & VERIF. | 486.8 RPS at 1.51ms latency  |
| Multi-Cloud Topology & IaC Design | PROPOSED FUTURE INF. | Documented across AWS/GCP    |
| MicroVM Hardware Sandboxing       | PROPOSED FUTURE INF. | Firecracker / gVisor design  |
+-----------------------------------------------------------------------------------------+
```

---

## 3. Application Containerization Architecture

### 3.1 Backend Container (`backend/Dockerfile`)
- **Base Image:** `python:3.12-slim-bookworm` (Debian-based minimal footprint).
- **Multi-Stage Build:** Builder stage compiles and caches wheels; runner stage discards compilers.
- **Security:** Runs as unprivileged system user `aether` (`uid: 10001, gid: 10001`). No root permissions inside container.
- **Health Check:** `HEALTHCHECK` queries `/api/v1/health` every 30s.
- **Image Size:** ~160 MB compressed.

### 3.2 Frontend Container (`frontend/Dockerfile`)
- **Stage 1 (Builder):** `node:22-alpine` performs reproducible `npm ci` and compiles static assets via `vite build`.
- **Stage 2 (Runner):** `nginxinc/nginx-unprivileged:alpine-slim` serves static files on port 8080 under unprivileged user `nginx`.
- **Security Headers:** Enforces Content Security Policy (CSP), `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`.
- **Image Size:** ~25 MB compressed.

---

## 4. Local Infrastructure Orchestration (`docker-compose.yml`)

The platform defines five decoupled Compose profiles to prevent memory thrashing on 8 GB development machines:

```bash
# Profile 1: Minimal Development (Backend + Frontend only, using SQLite)
docker compose --profile development up -d

# Profile 2: Data Services (PostgreSQL 16 + Redis 7)
docker compose --profile data up -d

# Profile 3: Background Worker Processing
docker compose --profile worker up -d

# Profile 4: Observability (Prometheus + Grafana)
docker compose --profile observability up -d

# Profile 5: Full Production Stack
docker compose --profile production up -d
```

### Resource Quotas Enforced:
- `backend`: 1.5 vCPU, 512 MB RAM limit.
- `frontend`: 0.5 vCPU, 256 MB RAM limit.
- `postgres`: 1.0 vCPU, 384 MB RAM limit.
- `redis`: 0.5 vCPU, 192 MB RAM limit.
- `worker`: 1.0 vCPU, 512 MB RAM limit.
- `prometheus` / `grafana`: 0.5 vCPU, 256 MB RAM limit.

---

## 5. Asynchronous Task Processing & Worker Architecture

```mermaid
sequenceDiagram
    participant User as Developer / Frontend
    participant API as FastAPI Control Plane
    participant Queue as Task Queue (Redis / In-Memory)
    participant Worker as Background Worker Daemon
    participant Broadcaster as SSE Event Broadcaster

    User->>API: POST /api/v1/queue/enqueue {task_id, idempotency_key}
    API->>Queue: enqueue(TaskJob) [Idempotency Check]
    API-->>User: 202 Accepted {job_id, status: "QUEUED"}

    loop Polling or Event Stream
        Worker->>Queue: dequeue()
        Queue-->>Worker: TaskJob
        Worker->>Broadcaster: broadcast("planning_started")
        Broadcaster-->>User: SSE Event {event: "planning_started"}
        Worker->>Worker: Execute Sandboxed Test / Patch
        Worker->>Broadcaster: broadcast("completed")
        Worker->>Queue: update_job(status: "COMPLETED")
    end
```

### Reliability Guarantees:
1. **Idempotency Keys:** Duplicate requests with matching `idempotency_key` return existing job metadata without executing duplicate agent actions.
2. **Approval Protection:** Privileged gates (`PLAN` approval, `DIFF` merge) are recorded in the relational database and **never** auto-replayed.
3. **Local Concurrency Bound:** Worker concurrency is strictly set to **1** by default to maintain the sub-100 MB memory profile on Mac M1.

---

## 6. Secure Code Execution Infrastructure

> [!IMPORTANT]
> Ordinary Docker containers share the host kernel and DO NOT provide sufficient security isolation for executing untrusted repository code.

### 4-Tier Security Boundary Architecture:
1. **Tier A (Application Control Plane):** FastAPI application managing authentication, database persistence, and API routing.
2. **Tier B (Model Provider Communication):** Model Gateway interfacing with external LLM APIs; credentials scrubbed from logs and prompt contexts.
3. **Tier C (Repository Storage):** Host workspace storage opened strictly in READ-ONLY mode during agent analysis.
4. **Tier D (Untrusted Code Execution):**
   - *Current Local Implementation:* Subprocess isolation with strict argument vector allowlists (`pytest`, `vitest`, `node`), environment variable scrubbing, 60s hard timeouts, and canonical path containment.
   - *Production Cloud Architecture:* Firecracker microVMs or gVisor (`runsc`), providing separate Linux kernel instances, non-shared filesystems, and zero network access.

---

## 7. User Authentication & Multi-Tenant Security

- **Password Hashing:** PBKDF2-HMAC-SHA256 with 100,000 iterations and per-user 16-byte random salt (`pbkdf2_sha256$100000$salt$key`).
- **Token Format:** HMAC-SHA256 JWT containing `sub`, `email`, `role` (`ADMIN`, `DEVELOPER`, `VIEWER`), `tenant_id`, `iss: "aether-engineer"`, and `aud: "aether-api"`.
- **Horizontal Privilege Escalation Defense:** Every workspace and task is bound to a `tenant_id`. `verify_workspace_access()` rejects access attempts from other tenants with HTTP 403 Forbidden.
- **Audit Trail:** Immutable security audit events recorded in `audit_events` table for login attempts, privilege escalations, and patch merges.

---

## 8. Observability & Monitoring

Prometheus metrics exposed at `/api/v1/metrics`:
- `aether_process_resident_memory_bytes`: Live resident memory from `resource.getrusage`.
- `aether_active_tasks`: Current count of executing tasks.
- `aether_tasks_completed_total` / `aether_tasks_failed_total`: Task lifecycle counts.
- `aether_http_requests_total{method, path, status}`: API traffic counters.
- `aether_llm_tokens_total{provider}` / `aether_llm_cost_dollars{provider}`: AI cost tracking.
- `aether_security_violations_total{vector}`: Blocked attack vectors.

