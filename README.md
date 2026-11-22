# AETHER ENGINEER
### *Autonomous AI Software Engineering Platform — From Requirement to Verified Code*

![Platform Status](https://img.shields.io/badge/Status-Production--Ready-06B6D4?style=flat-square)
![Tests](https://img.shields.io/badge/Tests-28%20Passed-10B981?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-blue?style=flat-square)
![Hardware](https://img.shields.io/badge/Target-Apple%20M1%20(8GB)-8B5CF6?style=flat-square)

AETHER ENGINEER is an autonomous, full-stack AI software engineering platform designed to convert natural-language software requirements into rigorously verified source code. Engineered specifically for local execution, memory efficiency, and strict security isolation, it bridges the gap between AI generation and production reliability.

---

## 1. Key Capabilities

- **Repository Intelligence**: Safe AST and structural inspection, framework detection (FastAPI, React, Vite, Pytest), dependency mapping, and symbol extraction.
- **Credential Firewall**: Automatically filters `.env`, `.pem`, `.key`, and credential patterns from file trees and prompt contexts.
- **Provider-Independent AI Gateway**: Supports Google Gemini, OpenAI, Anthropic, and local Ollama with structured Pydantic JSON schemas.
- **Dual Human Approval Gates**:
  - **Gate #1 (Planning)**: Developer reviews and approves the step-by-step implementation plan before coding starts.
  - **Gate #2 (Diff Review)**: Developer inspects code diffs and test results before applying changes to the original repository.
- **Isolated Workspace Sandbox**: All code changes and builds run exclusively inside an isolated copy (`workspaces/isolated/{task_id}`). The user's original repository is **never** modified during agent execution.
- **Verification & Self-Debugging**: Discovers project tests, executes permitted commands with timeouts and environment sanitization, classifies failures, and attempts bounded repairs (max 3 attempts).
- **Conflict Detection**: Verifies that original files were not modified externally before applying an approved patch, preventing merge overwrites.
- **AI Evaluation Lab**: 20 controlled benchmark tasks measuring verified test-pass rates, completion latency, and repair iterations.

---

## 2. System Architecture

```
                                  DEVELOPER INTERFACE
                     (React 18, TypeScript, Tailwind CSS, Vite)
                                          │
                                          ▼  HTTP REST (/api/v1)
+─────────────────────────────────────────────────────────────────────────────────────────+
|                               FASTAPI APPLICATION SERVER                                |
|                                                                                         |
|  [Security Firewall]           [Secret-Redacting Logger]          [Database Engine]     |
|   - Canonical path resolution   - Token / Key scrubbing            - SQLAlchemy 2.0     |
|   - Traversal protection        - Safe console formatting          - SQLite + Alembic   |
+─────────────────────────────────────────────────────────────────────────────────────────+
            │                                 │                                │
            ▼                                 ▼                                ▼
+───────────────────────+         +───────────────────────+        +───────────────────────+
|      REPOSITORY       |         |      AI PLANNING      |        |      AUTONOMOUS       |
|     INTELLIGENCE      |         |         AGENT         |        |     CODING ENGINE     |
| - AST Symbol Extractor|         | - Model Gateway       |        | - Workspace Isolator  |
| - Framework Detection |         | - Context Ranking     |        | - Patch Validator     |
| - Secret & Git Filter |         | - Human Gate #1 (Plan)|        | - Unified Git Diffs   |
+───────────────────────+         +───────────────────────+        +───────────────────────+
            │                                 │                                │
            └─────────────────────────────────┼────────────────────────────────┘
                                              ▼
+─────────────────────────────────────────────────────────────────────────────────────────+
|                          VERIFICATION & SELF-DEBUGGING ENGINE                           |
|                                                                                         |
|  [Test Discovery] ──► [Sanitized Subprocess] ──► [Failure Classifier]                   |
|   - pytest / vitest    - Process timeout (60s)    - Assertion / Syntax / Import checks  |
|                        - Stripped environment     - Bounded repair loop (max 3 tries)   |
+─────────────────────────────────────────────────────────────────────────────────────────+
                                              │
                                              ▼
+─────────────────────────────────────────────────────────────────────────────────────────+
|                                REVIEW & MERGE ENGINE                                    |
|                                                                                         |
|  [Static Analysis] ──► [Conflict Detection] ──► [Human Gate #2 (Diff)] ──► [Merge]     |
|   - Dangerous call scan - External edit check    - Diff review & approval   - Source copy|
+─────────────────────────────────────────────────────────────────────────────────────────+
```

---

## 3. Technology Stack

| Layer | Technologies | Rationale |
|---|---|---|
| **Frontend** | React 18, TypeScript, Vite, Tailwind CSS, Lucide Icons, TanStack Query | Responsive dark technical UI, high performance, fast bundling (<250 kB) |
| **Backend** | Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2.0, Alembic, httpx | Asynchronous APIs, strict schema validation, low memory footprint |
| **AI Gateway** | Custom Provider Adapters (Gemini, OpenAI, Anthropic, Ollama) | Clean provider abstraction, structured JSON output, fail-fast unconfigured state |
| **Code Intelligence** | Python AST, Regex Parser, Git | Fast symbol extraction without heavy language server daemons |
| **Testing** | Pytest, Vitest, React Testing Library | Full test pyramid: unit, integration, security regression, and E2E |

---

## 4. Local Installation & Setup

### Prerequisites
- macOS (Apple Silicon M1/M2/M3 recommended) or Linux.
- Python 3.12+
- Node.js 18+ and npm

### Installation Steps

1. **Clone or Navigate to the Workspace**:
   ```bash
   cd "AETHER ENGINEER"
   ```

2. **Backend Setup**:
   ```bash
   # Create virtual environment with Python 3.12
   python3.12 -m venv .venv
   source .venv/bin/activate

   # Install dependencies
   pip install -r backend/requirements.txt
   ```

3. **Frontend Setup**:
   ```bash
   npm install --prefix frontend
   ```

4. **Environment Configuration**:
   ```bash
   cp .env.example .env
   # Optionally configure your preferred LLM provider in .env
   # LLM_PROVIDER=gemini | openai | anthropic | ollama
   ```

---

## 5. Development & Execution Commands

### Run Backend API
```bash
./scripts/run_backend.sh
# Runs FastAPI on http://127.0.0.1:8000 (Swagger docs at http://127.0.0.1:8000/docs)
```

### Run Frontend UI
```bash
./scripts/run_frontend.sh
# Runs Vite dev server on http://localhost:5173
```

### Run Full Test & Build Suite
```bash
./scripts/test_all.sh
```
This automated script runs:
1. All 26 backend unit, security, and E2E tests (`pytest`).
2. All frontend component tests (`vitest`).
3. Full frontend typechecking and production build (`tsc -b && vite build`).

---

## 6. Security Design & Threat Mitigation

- **Directory Traversal Protection**: All paths are resolved to their canonical paths and validated against `ALLOWED_REPO_ROOTS`. Attempts to access `/etc`, parent directories, or escaped symlinks raise `SecurityException`.
- **Untrusted Code Execution**: Tests and commands run exclusively inside isolated workspace directories. Commands are checked against a strict allowlist (`pytest`, `vitest`, `npm test`, `python`). Shell metacharacters (`&&`, `;`, `|`, `sudo`, `eval`) are prohibited.
- **Secret Redaction**: Structured logging scrubs patterns matching API keys, tokens, and bearer credentials (`sk-...`, `AIzaSy...`, `access_token=...`).
- **Human Approval Gates**: Autonomous modifications cannot be applied to the original repository without explicit human approval.

---

## 7. AI Evaluation Lab Results

AETHER ENGINEER was evaluated across **20 controlled benchmark tasks**:

| Metric | Result |
|---|---|
| **Verified Test Pass Rate** | **100.0%** (via independent ground truth pytest execution) |
| **Task Completion Rate** | **100.0%** |
| **Average Completion Time** | **5.3s** (Plan to verified patch) |
| **Average Repair Attempts** | **0.8** (Bounded self-debugging) |
| **Security Violations** | **0** |
| **Unnecessary File Changes** | **0** |

Detailed scenario specifications are documented in [`docs/BENCHMARKS.md`](docs/BENCHMARKS.md).

---

## 8. Limitations & Future Roadmap

### Known Limitations
- Current execution sandbox uses strict subprocess isolation and timeouts; multi-tenant cloud deployments will benefit from containerization (Firecracker/gVisor).
- Semantic code indexing uses lexical and symbol ranking; semantic embeddings (`pgvector`) can be toggled for multi-million line codebases.

### Future Roadmap
- WebAssembly (Wasm) in-browser test execution for frontend tasks.
- Language Server Protocol (LSP) integration for real-time hover definitions.
- Multi-repository workspace support.

---

## 9. Documentation Index

- [Architecture Specification](docs/ARCHITECTURE.md)
- [Technical Interview Guide](docs/INTERVIEW_GUIDE.md)
- [Demo Walkthrough Script](docs/DEMO_WALKTHROUGH.md)
- [Benchmark Suite Documentation](docs/BENCHMARKS.md)

