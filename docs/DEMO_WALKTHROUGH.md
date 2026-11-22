# AETHER ENGINEER — Demo Walkthrough Script

Use this script during portfolio demonstrations, live coding interviews, or architectural presentations.

---

## 1. Quick Start (Terminal)

```bash
# Terminal 1: Start Backend API
./scripts/run_backend.sh

# Terminal 2: Start React Frontend
./scripts/run_frontend.sh
```

Navigate to: `http://localhost:5173`

---

## 2. Walkthrough Steps

### Step 1: System Overview & Status Check
- Open the **Dashboard**. Point out the hardware indicator (`Apple M1 8GB`), database status (`DB Connected`), and AI Gateway status (`AI: Configured | Unconfigured`).
- Emphasize the **Security Model**: "Isolated Copies Only — zero direct source edits."

### Step 2: Registering a Workspace
- Click **Workspaces** in the sidebar.
- Show the canonical path validation and explain that paths outside allowed development roots are strictly forbidden.
- Register or select the sample project.

### Step 3: Repository Intelligence Explorer
- Navigate to **Repo Explorer**.
- Show the detected technologies (e.g. FastAPI, React, Pytest).
- Point out that `.env` files, credentials, and `.gitignore` patterns are strictly filtered out to protect sensitive developer secrets.

### Step 4: Dispatching an Autonomous AI Task
- Open the **AI Task Console**.
- Submit the requirement:
  > *"Inspect this FastAPI application, identify the authentication bug, implement a reliable fix, add regression tests, and show the complete changes."*
- Click **Dispatch Task**.

### Step 5: Human Approval Gate #1 (Planning)
- Show the **Planning Engine** workspace:
  - Step 1: Fix token expiration in `auth.py`.
  - Step 2: Add regression tests in `test_auth.py`.
  - Risk assessment: `MEDIUM`.
- Explain: *"AETHER ENGINEER enforces a human-in-the-loop gate before any code generation begins."*
- Click **Approve & Execute**.

### Step 6: Isolated Sandboxing & Autonomous Coding
- Explain that the coding engine automatically created a sandboxed copy in `workspaces/isolated/{task_id}`.
- Switch to the terminal or file browser to prove that the original repository is 100% untouched.

### Step 7: Test Verification & Self-Debugging
- Open **Test & Verification**.
- Show the test discovery mechanism detecting `pytest`.
- Show the live failure capture: on initial run, the test caught an `AssertionError`.
- Show how the Self-Debugging Agent diagnosed the failure, proposed a targeted repair patch, and re-ran the test until it produced an exit code of `0` (Success).

### Step 8: Diff Review & Human Approval Gate #2
- Open **Diff Review**.
- Review the unified color-coded diff showing lines added and removed.
- Show the static analysis check confirming zero syntax errors and zero dangerous pattern escapes.
- Demonstrate **Conflict Detection**: if an external developer edited the original file, merge is blocked with an HTTP 409 Conflict.
- Click **Approve & Apply** to safely merge the verified patch into the original codebase.

### Step 9: Evaluation Lab
- Open the **Evaluation Lab**.
- Showcase the 20 repeatable benchmark tasks across 10 engineering categories.
- Run the benchmark suite to display real, verified test pass rates.

