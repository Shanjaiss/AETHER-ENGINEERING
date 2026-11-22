# AETHER ENGINEER — System Architecture & Design Specification

**Tagline:** *From Requirement to Verified Code.*

AETHER ENGINEER is an autonomous, production-oriented AI software engineering platform engineered specifically for local execution, resource efficiency, strict security boundaries, and reproducible verification.

---

## 1. High-Level Architecture Diagram

```
+-----------------------------------------------------------------------------------+
|                                 DEVELOPER UI                                      |
|            (React 18, TypeScript, Tailwind CSS, TanStack Query, Vite)             |
+-----------------------------------------------------------------------------------+
                                         │  HTTP / REST (FastAPI /api/v1)
                                         ▼
+-----------------------------------------------------------------------------------+
|                              FASTAPI BACKEND CORE                                 |
|                                                                                   |
|  [Security & Path Firewall]      [Secret Redacting Logger]    [Database Engine]   |
|   - Canonical path resolution     - Regex key scrubbing        - SQLAlchemy 2.0   |
|   - Traversal prevention          - Memory-safe buffering      - SQLite / Alembic |
+-----------------------------------------------------------------------------------+
                                         │
        ┌────────────────────────────────┼────────────────────────────────┐
        ▼                                ▼                                ▼
+───────────────────+          +───────────────────+          +───────────────────+
|   REPOSITORY      |          |    AI PLANNING    |          |    AUTONOMOUS     |
|  INTELLIGENCE     |          |       AGENT       |          |   CODING ENGINE   |
| - AST Symbol Extr |          | - Model Gateway   |          | - Workspace Copy  |
| - Git Status      |          | - Context Slicing |          | - File Boundary   |
| - Tech Detect     |          | - Plan Generation |          | - Patch Engine    |
| - Secret Exclude  |          | - Human Gate #1   |          | - Unified Diffs   |
+───────────────────+          +───────────────────+          +───────────────────+
        │                                │                                │
        └────────────────────────────────┼────────────────────────────────┘
                                         ▼
+───────────────────────────────────────────────────────────────────────────────────+
|                       VERIFICATION & SELF-DEBUGGING ENGINE                        |
|                                                                                   |
|  [Test Discovery] ──► [Sanitized Subprocess] ──► [Failure Classifier]             |
|   - pytest / vitest    - Resource & timeout limits - AST/Assertion categorization |
|                        - Strict command allowlist   - Bounded loop (max 3 tries)  |
+───────────────────────────────────────────────────────────────────────────────────+
                                         │
                                         ▼
+───────────────────────────────────────────────────────────────────────────────────+
|                         REVIEW & MERGE GATE ENGINE                                |
|                                                                                   |
|  [Static Analysis] ──► [Conflict Detection] ──► [Human Gate #2] ──► [Safe Merge]  |
|   - Dangerous call scan - External edit check    - Diff review       - Source update|
+───────────────────────────────────────────────────────────────────────────────────+
```

---

## 2. Core Subsystems

### A. Repository Intelligence Engine (`services/repo_intelligence/`)
- **Safe Traversal & Canonical Path Validation**: Rejects any path traversal (`..`, symlink redirection) outside explicitly allowlisted developer directories (`settings.ALLOWED_REPO_ROOTS`).
- **Secret & Credential Firewall**: Automatically ignores `.env*`, `*.pem`, `*.key`, `id_rsa*`, and AWS/GCP credential files from file indexing and LLM prompt context.
- **AST Symbol Extraction**: Uses Python's built-in `ast` module and TypeScript regex parsers to map functions, classes, and types without incurring the memory footprint of heavy language servers.
- **Context Ranking & Budgeting**: Scores codebase files using keyword relevance against user prompts, fitting code within strict token budgets.

### B. AI Planning Agent (`services/orchestrator/planning_agent.py`)
- **Gateway Abstraction**: Provider-independent model gateway supporting Google Gemini, OpenAI, Anthropic, and local Ollama.
- **Transparent Failure**: When credentials are not configured, raises a typed `LLMConfigurationError` rather than faking execution (Rule 15).
- **Structured Schema Enforcement**: Validates step-by-step plans using strict Pydantic models (`ImplementationPlanOutput`), requiring risk classification and predicted file modifications.
- **Human Approval Gate #1**: Workflow halts until the developer explicitly approves the plan.

### C. Autonomous Coding Engine (`services/coding_engine/`)
- **Isolated Workspace Sandbox**: All code edits take place exclusively in an isolated copy (`workspaces/isolated/{task_id}`). The user's original repository is **never** touched during plan execution.
- **Patch Engine (`patch_engine.py`)**: Validates patch targets against sandbox boundaries, generates standard unified git diffs, and computes before/after content.

### D. Verification & Self-Debugging Engine (`services/verification/`, `services/debugging/`)
- **Automated Test Discovery**: Discovers project test suites (`pytest`, `vitest`).
- **Subprocess Isolation**: Runs tests with strict timeouts (`ISOLATED_SANDBOX_TIMEOUT_SECONDS=60`), environment sanitization (stripping API keys and sensitive environment variables), and command allowlisting (`pytest`, `vitest`, `npm test`, `python`).
- **Failure Classification**: Categorizes failures (`ASSERTION_ERROR`, `SYNTAX_ERROR`, `IMPORT_ERROR`, `TYPE_ERROR`, `TIMEOUT_ERROR`).
- **Bounded Self-Debugging Loop**: Enforces `MAX_REPAIR_ATTEMPTS=3` to guarantee the agent never gets trapped in infinite repair recursion.

### E. Review & Safe Application Engine (`services/review/`)
- **Static Analysis & Security Warnings**: Scans diffs for dangerous functions (`eval`, `exec`, `os.system`, `subprocess(shell=True)`) and inadvertent secret commits.
- **Conflict Detection**: Verifies that original repository files have not changed externally since the task started. If modified, merge is blocked with HTTP 409 Conflict.
- **Human Approval Gate #2**: Developer must explicitly approve the patch diff before any files in the original repository are updated.

### F. AI Evaluation Lab (`services/evaluation/`)
- **20 Controlled Benchmark Tasks**: Repeatable evaluation suite spanning bug fixing, test generation, endpoint implementation, refactoring, TypeScript types, and validation.
- **Objective Ground Truth Verification**: Metrics are computed exclusively from independent pytest test results—never fabricated.

---

## 3. Apple Silicon M1 (8GB) Memory Optimization

1. **Lightweight Tooling**: Direct Python standard library AST parsing rather than heavy external language servers.
2. **Minimal In-Memory Footprint**: SQLite database initially with zero background daemon overhead.
3. **No Heavy Vector DB by Default**: Context retrieval operates efficiently via lexical and symbol ranking; pgvector is reserved only for massive multi-million line codebases.
4. **Vite Frontend Bundling**: Fast compile and small production bundles (<250 kB total).

