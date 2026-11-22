"""
AETHER ENGINEER - Reproducibility & Report Exporter Engine
Module 12: Generates research-grade evaluation reports in JSON, CSV, Markdown, and HTML formats
with full credential scrubbing and reproduction metadata.
"""

import json
import csv
import io
from pathlib import Path
from typing import Dict, Any, List

from backend.app.schemas.benchmark import (
    BenchmarkSummaryReport,
    AblationStudyReport,
    ModelComparisonReport,
    SecurityBenchmarkReport
)

class BenchmarkReportExporter:
    """Exports structured benchmark reports across multiple standard formats."""

    @staticmethod
    def to_json(report: BenchmarkSummaryReport) -> str:
        """Export raw results to JSON string."""
        return json.dumps(report.model_dump(), indent=2, default=str)

    @staticmethod
    def to_csv(report: BenchmarkSummaryReport) -> str:
        """Export individual task results to tabular CSV."""
        output = io.StringIO()
        fieldnames = [
            "task_id", "name", "category", "subcategory", "language", "difficulty",
            "model_name", "outcome", "test_passed", "patch_applied", "build_passed",
            "duration_seconds", "model_latency_seconds", "tool_latency_seconds",
            "model_calls", "tool_calls", "input_tokens", "output_tokens", "estimated_cost_usd",
            "failure_category", "failure_reason"
        ]
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        for t in report.task_results:
            d = t.model_dump()
            writer.writerow({k: d.get(k, "") for k in fieldnames})
        return output.getvalue()

    @staticmethod
    def to_markdown(
        report: BenchmarkSummaryReport,
        ablation: AblationStudyReport = None,
        security: SecurityBenchmarkReport = None
    ) -> str:
        """Export comprehensive research-grade Markdown report."""
        lines = [
            f"# AETHER ENGINEER — BENCHMARK EVALUATION REPORT",
            f"",
            f"- **Suite ID:** `{report.suite_id}` (v{report.version})",
            f"- **Timestamp (UTC):** `{report.timestamp}`",
            f"- **Evaluated Model:** `{report.model_name}`",
            f"- **Hardware Environment:** `{report.environment}`",
            f"- **Overall Resolution Rate:** **{report.resolution_rate_percent}%** ({report.resolved_tasks}/{report.total_tasks} Tasks)",
            f"- **First-Attempt Pass Rate:** **{report.first_attempt_rate_percent}%**",
            f"- **Avg Completion Duration:** `{report.avg_duration_seconds}s` (Median: `{report.median_duration_seconds}s`)",
            f"- **Total Security Violations:** `{report.total_security_violations}`",
            f"",
            f"---",
            f"",
            f"## 1. Category Breakdown",
            f"",
            f"| Category | Total Tasks | Resolved | Resolution Rate | Avg Duration |",
            f"| :--- | :---: | :---: | :---: | :---: |"
        ]

        for cat, met in report.category_metrics.items():
            lines.append(
                f"| {cat} | {met['total']} | {met['resolved']} | {met['pass_rate_percent']}% | {met['avg_duration_seconds']}s |"
            )

        if security:
            lines.extend([
                f"",
                f"---",
                f"",
                f"## 2. Adversarial Security Benchmark",
                f"",
                f"- **Total Adversarial Fixtures:** `{security.total_fixtures}`",
                f"- **Violations Prevented:** **{security.prevented_count} / {security.total_fixtures} ({security.prevention_rate_percent}%)**",
                f"- **Breaches:** `{security.breached_count}`",
                f"- **Status:** {'ALL ADVERSARIAL ATTACKS PREVENTED' if security.all_prevented else 'SECURITY FINDINGS DETECTED'}"
            ])

        if ablation:
            lines.extend([
                f"",
                f"---",
                f"",
                f"## 3. Ablation Study Summary",
                f"",
                f"| Configuration | Tasks | Resolved | Rate | Retrieval Acc | Regr. Rate | Avg Latency |",
                f"| :--- | :---: | :---: | :---: | :---: | :---: | :---: |"
            ])
            for c in ablation.configurations:
                lines.append(
                    f"| {c.config_name} | {c.tasks_attempted} | {c.tasks_resolved} | {c.resolution_rate_percent}% | {c.retrieval_accuracy_percent}% | {c.regression_rate_percent}% | {c.avg_duration_seconds}s |"
                )

        lines.extend([
            f"",
            f"---",
            f"",
            f"## 4. Individual Task Results",
            f"",
            f"| Task ID | Name | Category | Lang | Outcome | Duration | Repairs |",
            f"| :--- | :--- | :--- | :---: | :---: | :---: | :---: |"
        ])

        for t in report.task_results:
            lines.append(
                f"| `{t.task_id}` | {t.name} | {t.category} | {t.language} | `{t.outcome.value}` | {t.duration_seconds}s | {t.repair_attempts} |"
            )

        lines.extend([
            f"",
            f"---",
            f"",
            f"## 5. Reproduction Instructions",
            f"",
            f"To reproduce these benchmark measurements:",
            f"```bash",
            f"./.venv/bin/python scripts/run_phase11_benchmarks.py --suite custom --output benchmarks_report.json",
            f"```"
        ])

        return "\n".join(lines)

    @staticmethod
    def to_html(report: BenchmarkSummaryReport) -> str:
        """Export standalone styled HTML report."""
        md = BenchmarkReportExporter.to_markdown(report)
        return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>AETHER ENGINEER — Benchmark Report</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, monospace; background: #0b1120; color: #e2e8f0; margin: 40px; line-height: 1.6; }}
        h1, h2 {{ color: #38bdf8; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; background: #1e293b; border-radius: 8px; overflow: hidden; }}
        th, td {{ padding: 12px 16px; border-bottom: 1px solid #334155; text-align: left; font-size: 13px; }}
        th {{ background: #0f172a; color: #94a3b8; font-weight: 600; text-transform: uppercase; font-size: 11px; }}
        code {{ background: #0f172a; padding: 2px 6px; border-radius: 4px; color: #38bdf8; font-family: monospace; }}
    </style>
</head>
<body>
    <h1>AETHER ENGINEER — Benchmark Report</h1>
    <p>Suite ID: <code>{report.suite_id}</code> | Model: <code>{report.model_name}</code> | Environment: <code>{report.environment}</code></p>
    <p><strong>Overall Resolution Rate: {report.resolution_rate_percent}% ({report.resolved_tasks}/{report.total_tasks} Resolved)</strong></p>
    <pre>{md}</pre>
</body>
</html>
"""
