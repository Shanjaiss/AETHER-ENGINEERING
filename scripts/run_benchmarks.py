import os
import sys
import json
import time
import resource
from pathlib import Path

# Add project root to sys.path
root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir))

from backend.app.core.database import SessionLocal
from backend.app.services.evaluation.benchmark_runner import BenchmarkRunner

def get_memory_mb():
    # On macOS ru_maxrss is in bytes
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    if sys.platform == 'darwin':
        return rss / (1024 * 1024)
    else:
        return rss / 1024

def main():
    mem_before_mb = get_memory_mb()
    print(f"[*] Initial Memory (RSS): {mem_before_mb:.2f} MB")

    db = SessionLocal()
    try:
        runner = BenchmarkRunner(db)
        print(f"[*] Starting full 20-benchmark evaluation suite...")
        start_time = time.perf_counter()
        
        report = runner.run_suite()
        total_time = time.perf_counter() - start_time

        mem_after_mb = get_memory_mb()
        print(f"[*] Completed 20 benchmarks in {total_time:.2f}s")
        print(f"[*] Peak Memory (RSS): {mem_after_mb:.2f} MB")
        
        print("\n" + "="*60)
        print("          BENCHMARK EVALUATION SUMMARY")
        print("="*60)
        print(f"Total Attempted:      {report.total_benchmarks_run}")
        passed_count = sum(1 for r in report.runs if r.test_passed)
        print(f"Verified Passed:      {passed_count}")
        print(f"Failed:               {report.total_benchmarks_run - passed_count}")
        print(f"Pass Rate:            {report.verified_pass_rate_percent}%")
        print(f"Average Duration:     {report.avg_duration_seconds}s per task")
        print(f"Security Violations:  {report.total_security_violations}")
        print(f"Model / Engine:       {report.model_name}")
        print(f"Environment:          {report.environment}")
        print("\nCategory Breakdown:")
        for cat, data in report.category_breakdown.items():
            print(f"  - {cat:<24}: {data['passed']}/{data['total']} passed ({data['pass_rate']}%)")

        print("\nIndividual Runs:")
        for r in report.runs:
            status_str = "PASSED" if r.test_passed else "FAILED"
            print(f"  [{status_str}] {r.benchmark_id}: {r.name:<35} ({r.duration_seconds}s)")

        # Save report JSON
        output_path = root_dir / "benchmarks_report.json"
        with open(output_path, "w") as f:
            f.write(report.model_dump_json(indent=2))
        print(f"\n[*] Report saved to {output_path}")

    finally:
        db.close()

if __name__ == "__main__":
    main()
