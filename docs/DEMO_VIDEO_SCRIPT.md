# AETHER ENGINEER — Professional Demo Video Scripts & Presentation Guide
**Tagline:** From Requirement to Verified Code  
**Platform Target:** Apple Silicon Mac M1 (8 GB Unified Memory)  
**Project Version:** v1.0.0-rc.1  

---

## Overview

This guide provides verbatim scripts, screen directions, and narrative pacing for four demo video formats:
1. **5-Minute Technical Deep Dive:** For Senior Technical Interviewers, Staff AI Engineers, and Engineering Directors.
2. **2-Minute Executive / Recruiter Pitch:** For Technical Recruiters, Hiring Managers, and Portfolio Reviews.
3. **60-Second Fast-Paced Reel / Short:** For LinkedIn, Twitter/X, and fast portfolio skimming.
4. **30-Second Elevator Pitch:** For networking calls, career fairs, and live introductions.

---

## 1. 5-Minute Technical Deep Dive Script

### Target Duration: 5:00 minutes
### Visual Setup:
- Left Half: VS Code / Terminal with Apple Silicon Mac M1 activity monitor.
- Right Half: Chrome browser at `http://localhost:5173` (AETHER ENGINEER React UI).

---

### [0:00 - 0:45] Act 1: The Engineering Problem & Architectural Philosophy
**Visual:**
- Camera on speaker or screen recording showing `AETHER ENGINEER` Dashboard.
- Terminal showing:
  ```bash
  uname -m  # Displays: arm64 (Apple Silicon Mac M1)
  ./scripts/profile_system.py
  ```
- Terminal output shows RSS baseline memory: `65.02 MB`.

**Spoken Script:**
> *"Most AI coding demos today suffer from three fundamental flaws: they are glorified chat boxes, they hallucinate code that is never tested, and they edit source code directly on the host machine without sandboxing, governance, or blast-radius analysis.*
>
> *I built **AETHER ENGINEER** to solve this. Its tagline is **'From Requirement to Verified Code'**.*
>
> *AETHER ENGINEER is an autonomous AI software engineering platform engineered specifically to run production workflows locally on an Apple Silicon Mac M1 with just 8 GB of unified memory. Notice our baseline memory right now: 65 megabytes. Zero heavy background daemons, zero external paid API requirements, and 100% deterministic, verifiable execution."*

---

### [0:45 - 1:45] Act 2: AST Repository Intelligence & Task Understanding
**Visual:**
- Switch to UI: Navigate to **Engineering Workspace**.
- In the file tree, click through `backend/app/core/auth.py`. Show AST symbol badges (`class`, `def`, call sites).
- Click **Run Task Understanding** with input:
  `"Fix JWT expiration defect where expired tokens are accepted, add regression test, and verify with pytest."`

**Spoken Script:**
> *"Let's see what happens when a software engineer submits an autonomous task. Before any LLM writes a single line of code, AETHER ENGINEER invokes its **Repository Intelligence Engine**.*
>
> *In under 60 milliseconds, it scans the repository tree, parses Python and TypeScript Abstract Syntax Trees, and extracts cross-file symbol definitions and call sites. It immediately detects that `decode_token` in `auth.py` is referenced across multiple routes.*
>
> *Our **Task Understanding Classifier** categorizes the request as a `BUG_FIX` with `HIGH` risk, automatically synthesizing three measurable Acceptance Criteria: isolating root cause, writing an inverted regression test, and achieving an exit code of 0 across the entire test suite."*

---

### [1:45 - 2:30] Act 3: Topological DAG Planning & Human Governance Gate #1
**Visual:**
- UI displays the generated DAG Plan:
  - Step 1: Baseline regression test isolation.
  - Step 2: Source modification in `auth.py`.
  - Step 3: Pytest verification and self-debugging validation.
- Highlight the **Approval Gate**: UI button **`[Approve & Execute]`** is active; execution is halted until clicked.
- Click **`[Approve & Execute]`**.

**Spoken Script:**
> *"Next is the **Topological DAG Planner**. Instead of unstructured text generation, AETHER decomposes the engineering task into a directed acyclic graph. It runs cycle detection and scope-creep analysis, ensuring the agent doesn't touch unrequested files.*
>
> *Notice our first governance gate: **Plan Approval Gate**. AETHER ENGINEER enforces human-in-the-loop control. The autonomous engine cannot touch the codebase until an engineer explicitly approves the architectural plan. Let's approve."*

---

### [2:30 - 3:30] Act 4: Sandboxed Code Modification & Self-Debugging Verification Loop
**Visual:**
- UI switches to **Execution Timeline**.
- Split screen shows the original repo folder vs `workspaces/isolated/` sandbox.
- Live test runner shows:
  - Iteration 1: Initial test fails with `AssertionError: DID NOT RAISE <class 'ValueError'>`.
  - Iteration 2: Self-Debugging Agent analyzes traceback, generates patch, applies unidiff.
  - Iteration 3: Verification test re-runs: `2 passed in 217ms (Exit code: 0)`.

**Spoken Script:**
> *"Now the autonomous coding begins. Look closely at the filesystem: the source repository is completely untouched. All modifications occur in an isolated quarantine sandbox.*
>
> *Our Patch Engine validates boundary security, preventing path traversal attacks like `../../etc/passwd` and symlink escapes.*
>
> *Here is the core differentiator: the **Verification & Self-Debugging Engine**. The initial regression test fails as expected. The agent doesn't give up or claim it's done. It parses the pytest traceback, isolates the missing timestamp comparison, applies a targeted 26-line unidiff, and re-executes pytest. Only when real execution exits with code 0 does the task proceed."*

---

### [3:30 - 4:15] Act 5: Unified Diff Review, Conflict Detection & Safe Merge
**Visual:**
- UI opens **Diff Review**.
- Rich side-by-side color-coded unified diff showing exact changes in `auth_service.py`.
- Highlight **Conflict Detection Badge**: `No Conflicts Detected (Clean Merge)`.
- Click **`[Approve & Merge]`**.
- Terminal shows git diff on main branch confirming verified patch applied cleanly.

**Spoken Script:**
> *"Now we reach Human Governance Gate #2: **Diff Review**. The developer reviews a syntax-highlighted unified diff showing exactly what changed.*
>
> *Our Review Engine runs an AST safety audit to ensure no secrets leaked and no unauthorized files were modified. It also performs three-way conflict detection: if a teammate modified the file while the agent was working, merge is blocked with an HTTP 409 Conflict.*
>
> *We approve the diff, and the patch is safely applied to the target repository."*

---

### [4:15 - 5:00] Act 6: Scientific Benchmarks, SWE-bench & Production Metrics
**Visual:**
- Navigate to **Evaluation Lab** and **Settings (System Telemetry)**.
- Show Benchmark Card: `50/50 Custom Tasks Resolved (100%)`.
- Show Security Card: `12/12 Adversarial Injections Prevented (100%)`.
- Show Prometheus Metrics & Load Test Stats: `486.8 req/sec`, `1.51 ms median latency`, `67.2 MB RSS`.

**Spoken Script:**
> *"Finally, AETHER ENGINEER is backed by rigorous empirical science. In our Evaluation Lab, we run a 50-task benchmark across Python, TypeScript, and JavaScript, achieving a 100% resolution rate with full independent verification.*
>
> *Our SWE-bench Lite adapter runs against real GitHub issues, and our 12-vector adversarial security harness blocks directory traversal, symlink escapes, and prompt injection with 100% prevention.*
>
> *Under the hood: SQLAlchemy connection pooling, PBKDF2 authentication, Server-Sent Events for real-time streaming, Prometheus metrics, and multi-stage containerization.*
>
> *All 74 backend tests and frontend suites pass in under 16 seconds on an 8 GB Mac M1. AETHER ENGINEER transforms autonomous software engineering from a speculative demo into a reliable, verifiable reality. Thank you."*

---

## 2. 2-Minute Executive / Recruiter Pitch Script

### Target Duration: 2:00 minutes
### Visual:
- Fast cuts between:
  1. Terminal running `./scripts/run_recruiter_demo.py --scenario all` (1.2s total run).
  2. UI showing the DAG plan, diff review, and evaluation lab metrics.

**Spoken Script:**
> *"Hi, I'm excited to present **AETHER ENGINEER**, an autonomous AI software engineering platform built with the philosophy: **'From Requirement to Verified Code.'**
>
> *Unlike standard AI coding assistants that generate untracked code directly in your editor, AETHER ENGINEER operates as a self-evaluating autonomous engineer with human-in-the-loop governance.
>
> *Here is our live demonstration running on an Apple Silicon Mac M1 with 8 GB of memory. In just 1.2 seconds, it executes three full end-to-end engineering lifecycles:*
>
> *First, Scenario A: a critical JWT expiration bug in a FastAPI backend. AETHER inspects the AST, generates a topological DAG plan, awaits engineer approval, applies a patch in an isolated sandbox, verifies the fix with pytest, and generates a clean unified diff.*
>
> *Second, Scenario B: implementing cursor pagination and request validation from scratch, adding unit tests that pass with zero regressions.*
>
> *Third, Scenario C: building a React state management component with full TypeScript typing.*
>
> *AETHER ENGINEER is built for enterprise safety: 20 security attack vectors are audited and blocked, including path traversal and prompt injection. It features PBKDF2 security, JWT authentication, Prometheus telemetry, and a scientific evaluation lab that scores 50 out of 50 on real engineering benchmarks.*
>
> *Peak memory usage is only 67 megabytes—well below our 150-megabyte budget. The entire platform is production-ready, fully tested across 74 automated tests, and ready for deployment. I look forward to discussing how this architecture can bring rigor to your engineering team."*

---

## 3. 60-Second Fast-Paced Reel / Short

### Target Duration: 0:60 minutes
### Audio: Upbeat, modern electronic background track.
### Visual: Dynamic split screens and speed-ramped capture.

| Time | Visual | Voiceover |
| :--- | :--- | :--- |
| **0:00 - 0:10** | Terminal typing: `uname -m && ./scripts/profile_system.py`. Memory counter: `65 MB`. | *"Can an autonomous AI software engineer run locally on an 8GB Mac M1 without burning cloud dollars or hallucinating broken code? Meet AETHER ENGINEER."* |
| **0:10 - 0:25** | UI DAG plan pops up -> engineer clicks **Approve** -> Sandbox spinner -> Pytest failure turning green. | *"Step 1: AST static analysis. Step 2: Topological DAG planning. Step 3: Human approval gate. Step 4: Quarantined sandbox coding with bounded self-repair."* |
| **0:25 - 0:40** | Color-coded unified diff viewer -> Conflict check badge -> Green merge checkmark. | *"AETHER doesn't just guess; it runs real test suites. If a test fails, it diagnoses the traceback, self-repairs, and verifies exit code 0 before showing you a color-coded unified diff."* |
| **0:40 - 0:50** | Evaluation Lab: `50/50 Benchmarks Passed` / `12/12 Security Attacks Blocked`. | *"Audited across 20 security vectors, zero path escapes, 50 out of 50 benchmark tasks resolved, and full SWE-bench adapter support."* |
| **0:50 - 1:00** | GitHub repo / Release Candidate `v1.0.0-rc.1` badge. | *"74 tests passing. From Requirement to Verified Code. Check out the link in my profile for the full source code."* |

---

## 4. 30-Second Elevator Pitch

### Target Duration: 0:30 minutes
### Format: Direct spoken pitch for conversational introductions.

> *"I designed and built **AETHER ENGINEER**, an autonomous AI software engineering platform that takes natural language requirements all the way to verified code.
>
> *Rather than editing code unsafely, AETHER builds an AST call graph, creates a topological execution DAG, pauses for human approval, and executes code inside quarantined subprocess sandboxes with automated pytest self-debugging.
>
> *It runs entirely locally on an Apple Silicon Mac M1 under a 150-megabyte memory budget, scores 100% across 50 engineering benchmarks, blocks 12 adversarial injection vectors, and includes enterprise RBAC and Prometheus telemetry. It’s fully open-source with 74 passing tests."*

---

## 5. Production Recording Checklist

- [ ] Display resolution set to 1920x1080 (1080p) or 2560x1440 (1440p).
- [ ] Font size in VS Code and Terminal set to 16px or 18px for readability.
- [ ] Browser zoom level set to 110% or 125%.
- [ ] Dark theme active across UI and Terminal (matching AETHER ENGINEER Slate/Blue palette).
- [ ] Clean terminal prompt with clean git status.
- [ ] Pre-run `./scripts/test_all.sh` to ensure warm cache and zero errors.
- [ ] Audio recorded via dedicated dynamic or condenser microphone with pop filter.

