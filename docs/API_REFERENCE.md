# AETHER ENGINEER — REST API Reference
### *OpenAPI / REST Endpoint Specification (`/api/v1`)*

This document provides complete documentation for the REST API endpoints provided by the AETHER ENGINEER platform.

All endpoints are hosted under the base URL prefix: `http://localhost:8000/api/v1` (with interactive Swagger documentation available at `http://localhost:8000/docs`).

---

## 1. System Health & Status

### `GET /api/v1/health`
Returns the operational health of the application, database connectivity, and configured AI model provider.

**Response (200 OK):**
```json
{
  "status": "ok",
  "version": "0.1.0",
  "environment": "development",
  "database_connected": true,
  "llm_configured": true,
  "llm_provider": "gemini",
  "details": {
    "target_platform": "Apple Silicon Mac M1 (8 GB RAM)",
    "database_engine": "sqlite"
  }
}
```

---

## 2. Workspaces (`/api/v1/workspaces`)

### `GET /api/v1/workspaces`
Lists all registered developer workspaces.

**Response (200 OK):**
```json
[
  {
    "id": "ws-12345",
    "name": "My Project",
    "path": "/Users/user/Projects/my_project",
    "is_active": true,
    "metadata_json": {},
    "created_at": "2026-11-22T08:00:00Z",
    "updated_at": "2026-11-22T08:00:00Z",
    "repositories": []
  }
]
```

### `POST /api/v1/workspaces`
Registers a new local workspace. Enforces canonical path validation against `ALLOWED_REPO_ROOTS`.

**Request Body:**
```json
{
  "name": "Auth Microservice",
  "path": "/Users/user/Projects/auth_service"
}
```

**Responses:**
- `201 Created`: Workspace successfully registered.
- `400 Bad Request`: Directory does not exist on disk.
- `403 Forbidden`: Directory escapes allowlisted repository roots (Directory Traversal Defense).

### `GET /api/v1/workspaces/{workspace_id}`
Retrieves details for a specific workspace.

### `DELETE /api/v1/workspaces/{workspace_id}`
Removes a workspace and any associated task metadata.

---

## 3. Repositories (`/api/v1/repositories`)

### `POST /api/v1/repositories/import`
Imports a local Git or directory repository into a workspace. Automatically performs AST inspection, framework detection (FastAPI, React, Vite, Pytest), and file inventory.

**Request Body:**
```json
{
  "workspace_id": "ws-12345",
  "path": "/Users/user/Projects/auth_service"
}
```

**Response (201 Created):**
```json
{
  "id": "repo-98765",
  "workspace_id": "ws-12345",
  "name": "auth_service",
  "path": "/Users/user/Projects/auth_service",
  "is_git": true,
  "default_branch": "main",
  "languages": { "Python": 12, "Markdown": 2 },
  "frameworks": ["FastAPI", "pytest"],
  "file_count": 14,
  "created_at": "2026-11-22T08:05:00Z"
}
```

### `GET /api/v1/repositories/{repo_id}/tree`
Returns the file tree structure. Automatically redacts and hides sensitive files (`.env`, `.pem`, `.key`, `id_rsa`).

### `GET /api/v1/repositories/{repo_id}/file?path=relative/path.py`
Retrieves file contents safely within workspace bounds.

---

## 4. Engineering Tasks (`/api/v1/tasks`)

### `GET /api/v1/tasks?workspace_id={workspace_id}`
Lists engineering tasks filtered optionally by workspace.

### `POST /api/v1/tasks`
Creates a new engineering task. Automatically triggers the Task Understanding Engine to compute intent, risk level, acceptance criteria, and ambiguity score.

**Request Body:**
```json
{
  "workspace_id": "ws-12345",
  "repository_id": "repo-98765",
  "title": "Fix token expiration defect in auth_service.py",
  "description": "Ensure verify_token() raises ValueError('Token has expired') when exp < time.time()."
}
```

**Response (201 Created):**
```json
{
  "id": "task-abcde",
  "workspace_id": "ws-12345",
  "repository_id": "repo-98765",
  "title": "Fix token expiration defect in auth_service.py",
  "description": "...",
  "status": "PLANNING",
  "risk_level": "HIGH",
  "acceptance_criteria": [
    { "id": "AC-01", "description": "Identify and isolate the root cause...", "passed": false },
    { "id": "AC-02", "description": "Implement regression test case...", "passed": false },
    { "id": "AC-03", "description": "All existing test suites pass...", "passed": false }
  ],
  "created_at": "2026-11-22T08:10:00Z"
}
```

### `GET /api/v1/tasks/{task_id}`
Returns task state, plan steps, approval gates, patches, and execution logs.

### `POST /api/v1/tasks/{task_id}/cancel`
Cancels a running task and cleans up any isolated sandbox processes.

---

## 5. Planning & Governance Gate #1 (`/api/v1/planning`)

### `POST /api/v1/planning/{task_id}/generate`
Triggers the Topological DAG Planner to construct multi-file implementation steps. Transitions task status to `AWAITING_PLAN_APPROVAL`.

### `POST /api/v1/planning/{task_id}/approve`
**Human Approval Gate #1:** Developer accepts or rejects the proposed DAG plan.

**Request Body:**
```json
{
  "decision": "APPROVED",
  "notes": "Plan looks solid. Proceed with isolated code generation."
}
```

---

## 6. Coding Engine (`/api/v1/coding`)

### `POST /api/v1/coding/{task_id}/execute`
Generates code patches using the configured model provider and applies them strictly inside the isolated workspace (`workspaces/isolated/{task_id}`). Transitions task to `VERIFYING`.

**Response (200 OK):**
```json
{
  "task_id": "task-abcde",
  "status": "VERIFYING",
  "patches_generated": 1,
  "diff_summary": "1 file changed, 8 insertions(+), 3 deletions(-)"
}
```

---

## 7. Verification & Self-Debugging (`/api/v1/verification`)

### `POST /api/v1/verification/{task_id}/run`
Executes test discovery and runs permitted test runners (`pytest`, `vitest`, `node`) in an isolated subprocess.
If tests fail, triggers the Failure Classifier and bounded self-debugging repair loop (up to 3 iterations).

**Response (200 OK):**
```json
{
  "task_id": "task-abcde",
  "exit_code": 0,
  "all_passed": true,
  "tests_run": 2,
  "tests_passed": 2,
  "duration_ms": 234,
  "stdout": "test_auth.py .. [100%]\n2 passed in 0.23s",
  "repair_iterations_used": 0
}
```

---

## 8. Review, Merge & Governance Gate #2 (`/api/v1/review`)

### `GET /api/v1/review/{task_id}/diff`
Computes unified git diffs between the verified isolated workspace and the original repository. Performs static security analysis on diff lines.

### `POST /api/v1/review/{task_id}/approve`
**Human Approval Gate #2:** Developer explicitly approves the diff.
Performs external file conflict checks: if original files changed externally during execution, returns `409 Conflict`. Otherwise, safely applies patches to the original repository.

**Request Body:**
```json
{
  "decision": "APPROVED",
  "notes": "Verified diffs and pytest pass. Merge to main."
}
```

---

## 9. Benchmarks & Evaluation Lab (`/api/v1/benchmarks`)

### `GET /api/v1/benchmarks`
Lists benchmark suites and tasks. Supports querying custom 50-task suite (`custom`) or legacy 20-task suite (`suite=legacy`).

### `POST /api/v1/benchmarks/run`
Executes benchmark tasks through the `IndependentEvaluationEngine`.

**Request Body:**
```json
{
  "suite": "custom",
  "limit": 50
}
```

**Response (200 OK):**
```json
{
  "total_tasks": 50,
  "resolved_tasks": 50,
  "resolution_rate_percent": 100.0,
  "first_attempt_rate_percent": 84.0,
  "avg_duration_seconds": 0.298,
  "median_duration_seconds": 0.291,
  "total_security_violations": 0,
  "category_metrics": {
    "Python Core & Algorithms": { "resolved": 10, "total": 10, "pass_rate_percent": 100.0 },
    "API & Backend Endpoints": { "resolved": 10, "total": 10, "pass_rate_percent": 100.0 },
    "Frontend & TypeScript": { "resolved": 10, "total": 10, "pass_rate_percent": 100.0 },
    "Advanced Bug Fixing": { "resolved": 10, "total": 10, "pass_rate_percent": 100.0 },
    "Refactoring & Architecture": { "resolved": 10, "total": 10, "pass_rate_percent": 100.0 }
  }
}
```

### `GET /api/v1/benchmarks/ablation`
Runs the 6-configuration ablation study (Config A baseline through Config F full platform) and returns comparative metrics.

### `GET /api/v1/benchmarks/security`
Runs the 12-fixture adversarial security attack suite and reports prevention statistics.

### `GET /api/v1/benchmarks/swe-bench-status`
Returns hardware gating and SWE-bench Lite adapter compatibility status for Apple Silicon Mac M1.

---

## 10. System Settings (`/api/v1/settings`)

### `GET /api/v1/settings`
Returns active system configuration, LLM provider, sandbox timeouts, and memory limits.

### `PUT /api/v1/settings`
Updates provider configuration (API keys are validated, never echoed back in plaintext).

