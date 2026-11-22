# AETHER ENGINEER — Portfolio Screenshot Catalog & Visual Asset Guide
**Platform:** Apple Silicon Mac M1  
**Project Version:** v1.0.0-rc.1  
**UI Resolution:** 2560x1440 (1440p) or 1920x1080 (1080p)  
**Theme:** Dark Slate / Deep Blue (Default Palette)  

---

## Overview

This directory catalogs the essential portfolio screenshots, video thumbnails, and visual assets showcasing the AETHER ENGINEER autonomous AI software engineering platform.

---

## Screenshot Inventory & Specifications

### 1. `01_dashboard_overview.png`
- **Page Route:** `http://localhost:5173/`
- **Components in View:**
  - System Status Bar: `Apple M1 (8GB)`, `DB: Connected`, `AI: Configured`, `Latency: 1.5ms`.
  - Metric Cards: Total Workspaces, Autonomous Tasks Completed, Benchmark Pass Rate (100%), Memory Footprint (67 MB).
  - Recent Autonomous Tasks Table with status badges (`COMPLETED`, `IN_PROGRESS`).
- **Recruiter Takeaway:** Clean, professional developer dashboard demonstrating real hardware telemetry, sub-70MB memory footprint, and production metrics.

### 2. `02_engineering_workspace_dag.png`
- **Page Route:** `http://localhost:5173/workspace`
- **Components in View:**
  - Left Panel: Interactive File Tree showing directory hierarchy with AST symbol badges.
  - Middle Panel: Task Understanding Card (`BUG_FIX`, `Risk: HIGH`, 3 synthesized Acceptance Criteria).
  - Topological Execution DAG: Visual node graph showing ordered steps with prerequisite arrows.
  - Human Approval Gate #1 Banner: `[AWAITING PLAN APPROVAL]` with `[Approve & Execute]` button.
- **Recruiter Takeaway:** Visual proof of topological DAG planning, cycle prevention, and human-in-the-loop governance before code modification.

### 3. `03_diff_viewer_approval_gate.png`
- **Page Route:** `http://localhost:5173/workspace` (Diff Review Tab)
- **Components in View:**
  - Side-by-side or unified color-coded diff viewer highlighting added/removed lines in `auth_service.py`.
  - Conflict Check Badge: `✓ No Conflicts Detected (Clean Merge)`.
  - Verification Evidence Drawer: `Pytest Execution: 2 passed in 217ms (Exit Code: 0)`.
  - Human Approval Gate #2 Banner: `[AWAITING DIFF APPROVAL]` with `[Approve & Merge]` button.
- **Recruiter Takeaway:** Demonstrates that no code touches production without verified unit test execution and explicit human review.

### 4. `04_evaluation_lab_benchmarks.png`
- **Page Route:** `http://localhost:5173/evaluation`
- **Components in View:**
  - Benchmark Summary Card: `50 / 50 Tasks Resolved (100.0%)`.
  - First-Attempt Pass Rate: `84.0%`.
  - Average Latency: `456 ms per task`.
  - Domain Breakdown Table: API Routing, State Machines, Auth, Pagination, Error Boundaries, Caching.
  - Export Buttons: `[Export JSON Report]`, `[Export CSV]`.
- **Recruiter Takeaway:** Scientific credibility and measurable engineering verification across multi-language benchmarks.

### 5. `05_swe_bench_adapter.png`
- **Page Route:** `http://localhost:5173/evaluation` (SWE-bench Tab)
- **Components in View:**
  - SWE-bench Lite Integration Card: `Environment Status: Verified`.
  - Benchmark Instance Selector: `psf__requests-2317`.
  - Execution Output: Golden fixture patch generation, prediction export in official SWE-bench JSONL schema.
- **Recruiter Takeaway:** Familiarity with state-of-the-art AI benchmarks and enterprise research standards.

### 6. `06_system_telemetry_settings.png`
- **Page Route:** `http://localhost:5173/settings`
- **Components in View:**
  - AI Gateway Model Selector: OpenAI GPT-4o, Anthropic Claude 3.5 Sonnet, Google Gemini 1.5 Pro, Ollama.
  - Allowed Repository Roots Containment Config: `["/Users/.../Documents"]`.
  - Live Prometheus Telemetry Panel: Real-time queries/sec, median latency, active connections, database pool stats.
- **Recruiter Takeaway:** Full-stack operational maturity with security sandboxing, rate limiting, and observability.

---

## Capture Procedure

To generate high-resolution screenshots:
1. Start backend and frontend services:
   ```bash
   ./scripts/run_backend.sh &
   ./scripts/run_frontend.sh &
   ```
2. Run the recruiter demo in another terminal to populate live execution data:
   ```bash
   .venv/bin/python3 scripts/run_recruiter_demo.py --scenario all
   ```
3. Open Chrome at `http://localhost:5173` with viewport sized to `1920x1080` (or `2560x1440`).
4. Capture full-page screenshots using Chrome DevTools (`Cmd + Shift + P` -> `Capture full size screenshot`).
5. Save captured PNGs to `docs/assets/` using the naming convention above.

