import os
import sys
import time
import resource
from pathlib import Path

# Add project root
root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir))

from backend.app.core.database import SessionLocal
from backend.app.services.repo_intelligence.scanner import RepositoryScanner
from backend.app.models import Workspace, Task, PlanStep, ExecutionRun, ApprovalGate, PatchDiff, BenchmarkRun

def get_dir_size_mb(path: Path) -> float:
    total = 0
    if not path.exists():
        return 0.0
    for entry in path.rglob("*"):
        if entry.is_file():
            try:
                total += entry.stat().st_size
            except (OSError, PermissionError):
                pass
    return round(total / (1024 * 1024), 2)

def get_rss_mb() -> float:
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    if sys.platform == 'darwin':
        return round(rss / (1024 * 1024), 2)
    return round(rss / 1024, 2)

def main():
    print("=" * 65)
    print("      AETHER ENGINEER — MAC M1 (8 GB) PERFORMANCE PROFILE")
    print("=" * 65)

    # 1. Disk & Artifact Footprints
    venv_size = get_dir_size_mb(root_dir / ".venv")
    db_size = round((root_dir / "aether_engineer.db").stat().st_size / (1024 * 1024), 3) if (root_dir / "aether_engineer.db").exists() else 0.0
    dist_size = get_dir_size_mb(root_dir / "frontend" / "dist")
    print(f"\n[1] Storage Footprints:")
    print(f"  - Python Virtualenv (.venv):     {venv_size} MB")
    print(f"  - Frontend Production (dist):    {dist_size} MB")
    print(f"  - SQLite Database File:          {db_size} MB")

    # 2. Memory Consumption
    idle_rss = get_rss_mb()
    print(f"\n[2] Memory Consumption (Process RSS):")
    print(f"  - Baseline Memory:               {idle_rss} MB (Mac M1 Budget: < 150 MB)")

    # 3. Repository Scanning & File Intelligence Performance
    scanner = RepositoryScanner(root_dir)
    t0 = time.perf_counter()
    summary = scanner.scan_summary()
    scan_duration = round((time.perf_counter() - t0) * 1000, 2)

    t0 = time.perf_counter()
    symbols = scanner.extract_symbols("backend/app/main.py")
    symbol_duration = round((time.perf_counter() - t0) * 1000, 2)

    print(f"\n[3] Repository Intelligence Latency:")
    print(f"  - Full Repo Tree Scan:           {scan_duration} ms ({summary['file_count']} files indexed)")
    print(f"  - AST Symbol Extraction:         {symbol_duration} ms ({len(symbols)} symbols indexed)")

    # 4. Database Query Latencies
    db = SessionLocal()
    try:
        t0 = time.perf_counter()
        ws_count = db.query(Workspace).count()
        task_count = db.query(Task).count()
        steps_count = db.query(PlanStep).count()
        exec_count = db.query(ExecutionRun).count()
        bench_count = db.query(BenchmarkRun).count()
        query_duration = round((time.perf_counter() - t0) * 1000, 2)

        print(f"\n[4] Database Query Performance:")
        print(f"  - Aggregate Multi-table Query:   {query_duration} ms")
        print(f"  - Records: {ws_count} Workspaces, {task_count} Tasks, {steps_count} PlanSteps, {exec_count} Executions, {bench_count} BenchmarkRuns")

    finally:
        db.close()

    peak_rss = get_rss_mb()
    print(f"\n[5] Resource Limits & Apple Silicon Verification:")
    print(f"  - Peak RSS during Audit:         {peak_rss} MB")
    print(f"  - Memory Budget Margin:          {round(150.0 - peak_rss, 2)} MB headroom below 150 MB target")
    print(f"  - Docker / Redis / PG:           0 heavy daemons required (Pure embedded SQLite + Subprocess Isolation)")

    print("=" * 65)

if __name__ == "__main__":
    main()
