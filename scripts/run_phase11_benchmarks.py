#!/usr/bin/env python3
"""
AETHER ENGINEER - Phase 11 Real-World Benchmarks & Evaluation CLI
Executes the custom 50-task benchmark suite, ablation study, model comparison,
SWE-bench adapter, and adversarial security benchmark on Apple Silicon Mac M1.
"""

import sys
import os
import argparse
import json
import resource
import time
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.app.core.database import SessionLocal
from backend.app.schemas.benchmark import BenchmarkTaskDefinition
from backend.app.services.evaluation.custom_benchmark_suite import CUSTOM_BENCHMARK_TASKS
from backend.app.services.evaluation.benchmark_engine import IndependentEvaluationEngine
from backend.app.services.evaluation.ablation_study import AblationStudyRunner
from backend.app.services.evaluation.model_comparison import ModelComparisonRunner
from backend.app.services.evaluation.security_benchmark import SecurityBenchmarkRunner
from backend.app.services.evaluation.swe_bench_adapter import SWEBenchAdapter
from backend.app.services.evaluation.report_exporter import BenchmarkReportExporter

def main():
    parser = argparse.ArgumentParser(description="AETHER ENGINEER Benchmark & Evaluation Harness")
    parser.add_argument("--suite", choices=["custom", "pilot", "held-out", "security", "ablation", "comparison", "swe-bench", "all"], default="custom", help="Suite to run")
    parser.add_argument("--limit", type=int, default=None, help="Max tasks to run")
    parser.add_argument("--output", type=str, default="benchmarks_report.json", help="Path to write JSON results")
    parser.add_argument("--export-md", type=str, default=None, help="Path to write Markdown report")
    parser.add_argument("--export-swe-bench", type=str, default=None, help="Export predictions to SWE-bench JSONL")

    args = parser.parse_args()

    print("=" * 70)
    print("AETHER ENGINEER — PHASE 11 BENCHMARK & EVALUATION HARNESS")
    print("Platform: Apple Silicon Mac M1 (8 GB RAM)")
    print("=" * 70)

    db = SessionLocal()
    engine = IndependentEvaluationEngine(db=db)

    report_summary = None
    ablation_report = None
    security_report = None

    try:
        if args.suite in ("custom", "pilot", "held-out", "all"):
            raw_tasks = CUSTOM_BENCHMARK_TASKS
            if args.suite == "pilot":
                raw_tasks = [t for t in raw_tasks if t["id"] in ["py-01", "js-01", "api-01", "fe-01", "adv-01"]]
            elif args.suite == "held-out":
                raw_tasks = [t for t in raw_tasks if t.get("is_held_out") is True]

            if args.limit:
                raw_tasks = raw_tasks[:args.limit]

            task_defs = [BenchmarkTaskDefinition(**t) for t in raw_tasks]
            print(f"\n[1/4] Running Custom Benchmark Suite ({len(task_defs)} tasks)...")
            report_summary = engine.run_suite(task_definitions=task_defs)

            print("\n--- Custom Benchmark Results ---")
            print(f"Total Tasks:          {report_summary.total_tasks}")
            print(f"Resolved Tasks:       {report_summary.resolved_tasks}")
            print(f"Resolution Rate:      {report_summary.resolution_rate_percent}%")
            print(f"First-Attempt Rate:   {report_summary.first_attempt_rate_percent}%")
            print(f"Avg Duration:         {report_summary.avg_duration_seconds}s (Median: {report_summary.median_duration_seconds}s)")
            print(f"Security Violations:  {report_summary.total_security_violations}")
            print("\nCategory Performance:")
            for cat, met in report_summary.category_metrics.items():
                print(f"  • {cat:<32} {met['resolved']}/{met['total']} ({met['pass_rate_percent']}%) avg {met['avg_duration_seconds']}s")

        if args.suite in ("security", "all"):
            print("\n[2/4] Running Adversarial Security Benchmark (12 vectors)...")
            sec_runner = SecurityBenchmarkRunner()
            security_report = sec_runner.run_security_suite()
            print(f"Security Fixtures:    {security_report.total_fixtures}")
            print(f"Violations Prevented: {security_report.prevented_count}/{security_report.total_fixtures} ({security_report.prevention_rate_percent}%)")
            print(f"Breached Attacks:     {security_report.breached_count}")

        if args.suite in ("ablation", "all"):
            print("\n[3/4] Running Agent Ablation Study (6 configurations)...")
            abl_runner = AblationStudyRunner()
            ablation_report = abl_runner.run_ablation_study(task_sample_size=10)
            print("\nConfiguration Comparison:")
            for c in ablation_report.configurations:
                print(f"  • {c.config_name:<38} {c.resolution_rate_percent:>5}% res | {c.retrieval_accuracy_percent:>5}% retr | {c.avg_duration_seconds:>5}s")

        if args.suite in ("swe-bench", "all"):
            print("\n[4/4] Verifying SWE-bench Adapter & Hardware Gating...")
            status = SWEBenchAdapter.check_environment_support()
            print(f"System:              {status['system']} ({status['architecture']})")
            print(f"Memory:              {status['memory_gb']} GB")
            print(f"Adapter Mode:        {status['adapter_mode']}")
            if status["blocker_explanation"]:
                print(f"Hardware Gate:       {status['blocker_explanation'][:90]}...")

            # Run 1 native fixture
            adapter = SWEBenchAdapter()
            res = adapter.run_fixture_evaluation(
                instance_id="psf__requests-2317",
                patch_content="def prepare_method(method):\n    if isinstance(method, bytes):\n        return method.decode('utf-8')\n    return str(method)\n"
            )
            print(f"Fixture psf__requests-2317: {'RESOLVED' if res.resolved else 'FAILED'} in {res.execution_time_seconds}s")

        # Memory tracking
        peak_rss_mb = round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / (1024 * 1024), 2)
        print(f"\nPeak Memory RSS:      {peak_rss_mb} MB (Target ceiling: 150 MB)")

        # Export JSON
        if report_summary and args.output:
            out_p = Path(args.output)
            out_p.write_text(BenchmarkReportExporter.to_json(report_summary), encoding="utf-8")
            print(f"\nSaved raw JSON report to: {out_p.resolve()}")

        # Export Markdown
        if report_summary and (args.export_md or args.suite in ("custom", "all")):
            md_path = Path(args.export_md or "docs/PHASE_11_BENCHMARK_REPORT.md")
            md_content = BenchmarkReportExporter.to_markdown(report_summary, ablation_report, security_report)
            md_path.write_text(md_content, encoding="utf-8")
            print(f"Saved Markdown report to: {md_path.resolve()}")

    finally:
        db.close()

    print("\n=== BENCHMARK EXECUTION COMPLETED SUCCESSFULLY ===")

if __name__ == "__main__":
    main()

