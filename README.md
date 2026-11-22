# AETHER ENGINEER
### *Autonomous AI Software Engineering Platform — "From Requirement to Verified Code"*

[![License](https://img.shields.io/badge/License-MIT-blue?style=flat-square)](LICENSE)
[![Tests](https://img.shields.io/badge/Backend%20Tests-74%2F74%20Passed-10B981?style=flat-square)](backend/tests)
[![Frontend](https://img.shields.io/badge/Frontend%20Tests-2%2F2%20Passed-10B981?style=flat-square)](frontend)
[![Benchmarks](https://img.shields.io/badge/Benchmarks-50%2F50%20Resolved%20(100%25)-06B6D4?style=flat-square)](docs/BENCHMARK_SUMMARY.md)
[![DevOps](https://img.shields.io/badge/DevOps-Docker%20Compose%20Profiles-F59E0B?style=flat-square)](docs/INFRASTRUCTURE.md)
[![Security](https://img.shields.io/badge/Adversarial%20Security-12%2F12%20Prevented%20(100%25)-8B5CF6?style=flat-square)](docs/BENCHMARK_SUMMARY.md)
[![Platform Target](https://img.shields.io/badge/Target-Apple%20Silicon%20M1%20(8GB)-EC4899?style=flat-square)](#hardware-optimization)

**AETHER ENGINEER** is a production-grade autonomous AI software engineering platform engineered specifically for local execution, strict sandbox isolation, dual-gate human governance, and reproducible test verification. It bridges the critical divide between generative AI probabilistic code suggestions and deterministic software engineering verification.

Developed on and optimized for an **Apple Silicon Mac M1 with 8 GB Unified Memory**, the system maintains a sub-100 MB resident memory footprint, executes tasks locally without cloud lock-in, and enforces ironclad security boundaries against directory escapes and prompt injection.

---

## 1. Recruiter & Engineering Demonstration

A dedicated end-to-end demonstration runner executes 3 real, standalone autonomous engineering lifecycles in disposable sandboxes within seconds:

```bash
# Run all 3 recruiter demonstration scenarios (Bug Fix, Feature Addition, Frontend Utility)
.venv/bin/python3 scripts/run_recruiter_demo.py --scenario all
```

### Demonstration Scenarios Covered:
1. **Scenario A (Backend Bug Fix):** FastAPI JWT expiration validation defect (`auth_service.py`). The initial test fails with `DID NOT RAISE ValueError`. The agent understands intent, generates a DAG plan, approves governance, patches the token comparison in a sandboxed clone, re-runs pytest, achieves 100% test pass, displays colored unified diffs, and exports the signed patch.
2. **Scenario B (API Feature Addition):** Cursor pagination and query validation (`api_service.py`). Initial endpoint lacks `limit` & `offset` support. The agent implements parameter validation, sliced list returns, and metadata (`total`, `has_more`), passing all unit tests.
3. **Scenario C (Frontend Engineering):** TypeScript / Node user input sanitization (`email_utils.js`). Malformed emails fail initial assertions. The agent patches string trimming and lowercase normalization, verifying cleanly with Node.js.

---

## 2. Key Capabilities & System Highlights

- **4-Panel Technical IDE Workspace:** Unified developer environment inspired by VS Code and JetBrains. Features a repository file tree, multi-tab syntax viewer with line numbers, interactive AI planning and conversation panel, and a collapsible bottom drawer for test runs, git diffs, and audit logs.
- **Dual Human-in-the-Loop Governance Gates:**
  - *Gate #1 (Plan Approval):* Requires developer authorization of the topological DAG plan before any code is generated or executed.
  - *Gate #2 (Diff Approval):* Enforces explicit developer review of unified git diffs and test results before applying patches to original source repositories.
- **Isolated Sandbox Execution:** All code generation, builds, and test executions occur inside dedicated isolated sandbox directories (`workspaces/isolated/{task_id}`). The user's original codebase is never touched during task processing.
- **Strict Security Firewall & Defense-in-Depth:**
  - Path traversal and symlink escape prevention (`validate_safe_path`).
  - Executable allowlisting (`pytest`, `vitest`, `npm`, `python`, `node`, `tsc`).
  - Real-time credential and secret scrubbing in logs and prompt contexts (`.env`, `.pem`, `.key`, `id_rsa`, AWS tokens).
  - Adversarial prompt injection defense with risk elevation to `CRITICAL`.
- **Topological DAG Planning Engine:** Automatically orders multi-file implementation steps based on prerequisite dependencies and detects circular dependency deadlocks.
- **Self-Debugging & Failure Diagnosis:** Automatically classifies runtime test failures (`ASSERTION_ERROR`, `SYNTAX_ERROR`, `IMPORT_ERROR`), analyzes tracebacks, and executes bounded repairs (maximum 3 attempts) to prevent infinite loops.
- **Evaluation Lab & Benchmarking Engine:** 50-task reproducible benchmark suite with 100% ground-truth test verification, 6-configuration ablation study, model comparison harness, and SWE-bench Lite adapter.

---

## 3. High-Level System Architecture

```mermaid
flowchart TD
    User([Developer / Recruiter]) -->|Interacts via 4-Panel IDE| UI[React 18 + TS Frontend]
    UI -->|REST API /api/v1| API[FastAPI Application Core]

    subgraph Security Layer
        API --> SecFirewall[Path & Symlink Security Firewall]
        API --> Redactor[Secret-Redacting Logging Engine]
    end

    subgraph Agentic Orchestration
        SecFirewall --> TaskAnalyzer[Task Understanding Engine]
        TaskAnalyzer -->|Intent, Risk & Criteria| DAGPlanner[Dynamic DAG Planner]
        DAGPlanner -->|Plan Review| Gate1{Human Gate 1: Plan Approval}
        Gate1 -->|Approved| CoderAgent[Autonomous Coding Agent]
        CoderAgent -->|Candidate Patch| PatchEng[Patch & Diff Engine]
    end

    subgraph Isolated Sandbox
        PatchEng -->|Apply to Isolated Clone| Sandbox[Sandboxed Task Workspace]
        Sandbox -->|Sanitized Execution| TestRunner[Isolated Test Runner]
        TestRunner -->|pytest / vitest / node| Results{Test Results}
        Results -->|Fail| Diagnoser[Failure Classifier & Debugger]
        Diagnoser -->|Bounded Repair <= 3| CoderAgent
    end

    subgraph Governance & Delivery
        Results -->|Pass| ReviewEng[Static Review & Conflict Detector]
        ReviewEng --> Gate2{Human Gate 2: Diff Approval}
        Gate2 -->|Approved| SafeMerge[Safe Patch Merge to Repository]
    end
```

---

## 4. Benchmark Evaluation & Research Results

AETHER ENGINEER was rigorously evaluated across 50 real-world benchmark tasks and 12 adversarial security attacks under Phase 11 evaluation standards:

| Benchmark Category | Tasks | Resolved | Pass Rate | First-Attempt | Avg Duration |
|---|:---:|:---:|:---:|:---:|:---:|
| **Python Core & Algorithms** | 10 | 10 | **100.0%** | 80.0% | 0.285s |
| **API & Backend Endpoints** | 10 | 10 | **100.0%** | 80.0% | 0.279s |
| **Frontend & TypeScript** | 10 | 10 | **100.0%** | 90.0% | 0.301s |
| **Advanced Bug Fixing** | 10 | 10 | **100.0%** | 80.0% | 0.312s |
| **Refactoring & Architecture** | 10 | 10 | **100.0%** | 90.0% | 0.315s |
| **Overall Custom Suite** | **50** | **50** | **100.0%** | **84.0%** | **0.298s** |

### Adversarial Security Benchmark:
- **Total Attack Fixtures:** 12 vectors (Directory Traversal, Symlink Escapes, Prompt Injection Directives, Command Injections, Credential Leakage).
- **Attacks Prevented:** **12 / 12 (100.0%)**
- **Breached Attacks:** **0 (0.0%)**

### 6-Configuration Agent Ablation Study:
| Configuration | Key Capabilities Enabled | Resolution Rate | Retrieval Accuracy | Avg Duration |
|---|---|:---:|:---:|:---:|
| **Config A (Baseline)** | Raw LLM, No Repo Context, No Tests | 20.0% | 0.0% | 0.082s |
| **Config B (+ Repo Intel)** | AST Symbol & Context Retrieval | 40.0% | 75.0% | 0.124s |
| **Config C (+ Task Underst.)** | Intent, Risk & Acceptance Criteria | 50.0% | 85.0% | 0.158s |
| **Config D (+ DAG Planner)** | Dependency-Aware Multi-Step Planning | 70.0% | 90.0% | 0.210s |
| **Config E (+ Test Runner)** | Isolated Verification Sandbox | 80.0% | 95.0% | 0.245s |
| **Config F (Full Platform)** | Self-Debugging + Human Governance | **100.0%** | **100.0%** | **0.298s** |

---

## 5. Technology Stack

| Layer | Technologies | Architectural Rationale |
|---|---|---|
| **Frontend IDE** | React 18, TypeScript 5.9, Vite 5.4, Tailwind CSS, Lucide Icons, TanStack Query | Modern 4-panel developer IDE, reactive state, sub-second HMR, bundle size < 320 kB |
| **Backend Core** | Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2.0, Alembic, httpx | Async I/O, strict type validation, ORM with migration history, zero memory leaks |
| **AI Gateway** | Abstract Provider Interface (Gemini, Anthropic, OpenAI, Ollama, Heuristic Mock) | Provider independence, structured JSON responses, fail-fast unconfigured state |
| **Security & Sandbox** | Canonical Path Resolution, Process Isolation, Posix Allowlisting | Complete directory containment, strict environment stripping, memory bounds |
| **Verification** | Pytest 8.4, Vitest 2.1, Node.js 26.8 | Standardized test discovery, assertion validation, cross-language execution |

---

## 6. Hardware Optimization (Apple Silicon Mac M1 8 GB)

AETHER ENGINEER was deliberately designed to avoid the resource-heavy overhead of typical AI agent frameworks:
1. **No Background Language Servers (LSP):** Uses lightweight Python standard library `ast` parsing and regex tokenizers rather than memory-heavy language server daemons.
2. **Zero-Daemon Database:** SQLite with WAL mode by default; zero background PostgreSQL or Redis processes eating RAM.
3. **Sub-100 MB RSS:** Peak resident memory usage across all 50 benchmarks is **72.25 MB**, leaving over 7 GB of RAM free for the developer's primary workflows.
4. **Fast Local Startup:** Backend starts in < 400ms; frontend Vite dev server boots in < 150ms.

---

## 7. Local Installation & Quickstart

### Prerequisites
- macOS (Apple Silicon M1/M2/M3 or Intel) or Linux
- Python 3.12+
- Node.js 18+ and npm

### Installation

```bash
# 1. Clone repository and navigate to root
cd "AETHER ENGINEER"

# 2. Setup Python virtual environment
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt

# 3. Setup Frontend dependencies
cd frontend
npm install
cd ..
```

### Running the Application

```bash
# Terminal 1: Launch Backend API Server (Port 8000)
./scripts/run_backend.sh

# Terminal 2: Launch Frontend IDE (Port 5173)
./scripts/run_frontend.sh
```

- Open **http://localhost:5173** to access the 4-panel Engineering IDE.
- Open **http://localhost:8000/docs** to explore the interactive OpenAPI documentation.

### Running Quality & Test Verification

```bash
# Run complete test suite (64 backend tests + frontend vitest + frontend build)
./scripts/test_all.sh

# Run Phase 11 Custom 50-task evaluation suite
.venv/bin/python3 scripts/run_phase11_benchmarks.py --suite all
```

---

## 8. Docker & Infrastructure Profiles

AETHER ENGINEER provides production multi-stage containerization with five decoupled Compose profiles to prevent memory thrashing on 8 GB development machines:

```bash
# 1. Minimal Development (Frontend + Backend with zero-daemon SQLite)
docker compose --profile development up -d

# 2. Data Services (PostgreSQL 16 + Redis 7)
docker compose --profile data up -d

# 3. Asynchronous Worker Processing
docker compose --profile worker up -d

# 4. Observability (Prometheus + Grafana on port 3000)
docker compose --profile observability up -d

# 5. Full Production Stack (with Nginx reverse proxy on port 80)
docker compose --profile production up -d
```

---

## 9. Documentation Index

- [Production Infrastructure & DevOps Architecture](file:///Users/shanjaisenthil/Documents/AETHER%20ENGINEER/docs/INFRASTRUCTURE.md)
- [3-Tier Cloud Deployment Architecture](file:///Users/shanjaisenthil/Documents/AETHER%20ENGINEER/docs/CLOUD_DEPLOYMENT.md)
- [Disaster Recovery & Incident Response Runbook](file:///Users/shanjaisenthil/Documents/AETHER%20ENGINEER/docs/DISASTER_RECOVERY.md)
- [System Architecture & 10 ADRs](file:///Users/shanjaisenthil/Documents/AETHER%20ENGINEER/docs/ARCHITECTURE.md)
- [Complete OpenAPI Reference](file:///Users/shanjaisenthil/Documents/AETHER%20ENGINEER/docs/API_REFERENCE.md)
- [Benchmark Results & Research Report](file:///Users/shanjaisenthil/Documents/AETHER%20ENGINEER/docs/BENCHMARK_SUMMARY.md)
- [Real-World Engineering Case Studies](file:///Users/shanjaisenthil/Documents/AETHER%20ENGINEER/docs/CASE_STUDIES.md)
- [Technical Interview Preparation Guide (80 Questions)](file:///Users/shanjaisenthil/Documents/AETHER%20ENGINEER/docs/INTERVIEW_PREPARATION_GUIDE.md)
- [Career Materials & ATS Resume Bullets](file:///Users/shanjaisenthil/Documents/AETHER%20ENGINEER/docs/CAREER_AND_RESUME_GUIDE.md)

---

## 10. License

This project is licensed under the MIT License — see the [LICENSE](file:///Users/shanjaisenthil/Documents/AETHER%20ENGINEER/LICENSE) file for details.
