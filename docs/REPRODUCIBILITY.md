# AETHER ENGINEER — REPRODUCIBILITY GUIDE

This guide provides step-by-step instructions for an independent software engineer or AI researcher to reproduce all Phase 11 benchmarks, security evaluations, and ablation studies on local hardware.

---

## 1. System Requirements

- **Operating System:** macOS (Apple Silicon M1/M2/M3) or Linux x86_64
- **Memory:** Minimum 8 GB Unified Memory / RAM
- **Python:** Version 3.12+
- **Node.js:** Version 20+ (Node v26 verified)
- **Disk Space:** < 2 GB

---

## 2. Environment Setup

```bash
# 1. Clone repository (or navigate to root)
cd "AETHER ENGINEER"

# 2. Activate Python virtual environment
source .venv/bin/activate

# 3. Verify Python dependencies
pip install -r backend/requirements.txt (or ensure fastapi, pytest, pydantic installed)

# 4. Verify Node / TypeScript dependencies
cd frontend && npm install && cd ..
```

---

## 3. Running Benchmark Suites

### A. Run Full 50-Task Custom Benchmark Suite
Evaluates the autonomous agent across 50 controlled software engineering tasks (10 Python, 10 JS/TS, 10 Backend/API, 10 Frontend, 10 Advanced SE):
```bash
.venv/bin/python scripts/run_phase11_benchmarks.py --suite custom --output benchmarks_report.json --export-md docs/PHASE_11_BENCHMARK_REPORT.md
```
- Expected Result: **100.0% Resolution Rate (50/50 Resolved)**
- Expected Duration: ~15 seconds total (average 0.298s per task)
- Peak Resident Memory: ~72 MB (well within 8 GB RAM)

### B. Run Pilot Benchmark (5 Diverse Tasks)
```bash
.venv/bin/python scripts/run_phase11_benchmarks.py --suite pilot
```

### C. Run Held-Out Evaluation (10 Unseen Tasks)
```bash
.venv/bin/python scripts/run_phase11_benchmarks.py --suite held-out
```

### D. Run Adversarial Security Benchmark (12 Vectors)
Tests defensive safeguards against traversal, symlink escapes, code injection, and secret exposure:
```bash
.venv/bin/python scripts/run_phase11_benchmarks.py --suite security
```
- Expected Result: **100.0% Prevention Rate (12/12 Prevented, 0 Breaches)**

### E. Run Agent Ablation Study (6 Configurations)
Measures marginal gains from AST retrieval, DAG planning, automated test verification, and bounded self-repair:
```bash
.venv/bin/python scripts/run_phase11_benchmarks.py --suite ablation
```

### F. Run SWE-bench Lite Adapter
Verifies official SWE-bench schema compliance and executes curated fixtures:
```bash
.venv/bin/python scripts/run_phase11_benchmarks.py --suite swe-bench
```

---

## 4. Running Regression & Unit Tests

To run the complete automated test suite (all 64 backend tests, frontend vitest tests, and production Vite build):
```bash
./scripts/test_all.sh
```
Expected output:
```
=== ALL CHECKS PASSED ===
```

