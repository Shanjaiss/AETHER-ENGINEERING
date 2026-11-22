"""
AETHER ENGINEER - Phase 11 Automated Test Suite
Verifies the custom 50-task benchmark dataset, independent evaluation engine,
SWE-bench adapter, ablation study, model comparison, adversarial security, and report exporters.
"""

import json
import pytest
from pathlib import Path
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.schemas.benchmark import (
    BenchmarkTaskDefinition,
    EvaluationOutcome,
    FailureCategory
)
from backend.app.services.evaluation.custom_benchmark_suite import CUSTOM_BENCHMARK_TASKS
from backend.app.services.evaluation.benchmark_engine import IndependentEvaluationEngine
from backend.app.services.evaluation.swe_bench_adapter import SWEBenchAdapter
from backend.app.services.evaluation.ablation_study import AblationStudyRunner
from backend.app.services.evaluation.model_comparison import ModelComparisonRunner
from backend.app.services.evaluation.security_benchmark import SecurityBenchmarkRunner
from backend.app.services.evaluation.report_exporter import BenchmarkReportExporter

client = TestClient(app)

def test_custom_benchmark_dataset_integrity():
    """Verify all 50 custom benchmark tasks adhere to schema and have unique IDs."""
    assert len(CUSTOM_BENCHMARK_TASKS) == 50

    task_ids = set()
    categories = {
        "Python": 0,
        "JavaScript and TypeScript": 0,
        "Backend and API Engineering": 0,
        "Frontend Engineering": 0,
        "Advanced Software Engineering": 0
    }
    held_out_count = 0

    for t in CUSTOM_BENCHMARK_TASKS:
        # Pydantic schema validation
        task_def = BenchmarkTaskDefinition(**t)
        assert task_def.id not in task_ids, f"Duplicate task ID: {task_def.id}"
        task_ids.add(task_def.id)

        assert task_def.category in categories, f"Unknown category: {task_def.category}"
        categories[task_def.category] += 1

        assert len(task_def.initial_files) > 0
        assert len(task_def.test_files) > 0
        assert len(task_def.expected_files) > 0
        assert task_def.reference_fix is not None

        if task_def.is_held_out:
            held_out_count += 1

    # Exactly 10 tasks in each of the 5 categories
    for cat, count in categories.items():
        assert count == 10, f"Category {cat} has {count} tasks, expected 10"

    # Exactly 10 held-out evaluation tasks
    assert held_out_count == 10

def test_independent_evaluator_scoring_and_gates(tmp_path):
    """Verify the 7 evaluation gates and independent scoring on a sample task."""
    sample = next(t for t in CUSTOM_BENCHMARK_TASKS if t["id"] == "py-01")
    task_def = BenchmarkTaskDefinition(**sample)

    engine = IndependentEvaluationEngine(workspace_base=tmp_path)
    res = engine.evaluate_task(task_def)

    assert res.task_id == "py-01"
    assert res.outcome == EvaluationOutcome.RESOLVED
    assert res.patch_applied is True
    assert res.build_passed is True
    assert res.original_tests_passed is True
    assert res.acceptance_tests_passed is True
    assert res.security_violations == 0
    assert res.unrelated_files_modified == 0
    assert res.duration_seconds > 0

def test_hidden_acceptance_test_protection():
    """Verify that evaluator acceptance tests and reference fixes are never exposed to agent."""
    sample = next(t for t in CUSTOM_BENCHMARK_TASKS if t["id"] == "py-02")
    task_def = BenchmarkTaskDefinition(**sample)

    # Initial context only receives initial_files
    assert "test_acceptance" not in task_def.initial_files
    assert "test_json_loader.py" in task_def.test_files
    assert "test_json_loader.py" not in task_def.initial_files

def test_swe_bench_adapter_environment_check_and_fixture():
    """Verify SWE-bench adapter hardware check and curated fixture execution."""
    status = SWEBenchAdapter.check_environment_support()
    assert "memory_gb" in status
    assert "architecture" in status
    assert status["adapter_mode"] in ("NATIVE_FIXTURE_EVALUATION", "DOCKER_FULL", "ADAPTER_MOCK")

    adapter = SWEBenchAdapter()
    instances = adapter.load_curated_instances()
    assert len(instances) >= 2

    # Run localized evaluation on fixture
    res = adapter.run_fixture_evaluation(
        instance_id="psf__requests-2317",
        patch_content="def prepare_method(method):\n    if isinstance(method, bytes):\n        return method.decode('utf-8')\n    return str(method)\n"
    )
    assert res.instance_id == "psf__requests-2317"
    assert res.resolved is True
    assert res.patch_applied is True
    assert res.fail_to_pass_success is True

def test_ablation_study_configurations():
    """Verify 6-configuration agent ablation study."""
    runner = AblationStudyRunner()
    report = runner.run_ablation_study(task_sample_size=5)

    assert len(report.configurations) == 6
    config_names = [c.config_name for c in report.configurations]
    assert any("Config A" in n for n in config_names)
    assert any("Config F" in n for n in config_names)

    # Config F must outperform Config A
    config_a = report.configurations[0]
    config_f = report.configurations[5]
    assert config_f.resolution_rate_percent > config_a.resolution_rate_percent
    assert config_f.retrieval_accuracy_percent > config_a.retrieval_accuracy_percent

def test_model_comparison_runner_safety():
    """Verify model comparison runs without crashing when credentials are unconfigured."""
    runner = ModelComparisonRunner()
    report = runner.run_comparison(task_sample_size=2)

    assert len(report.models) >= 2
    assert report.models[0].resolved_tasks > 0

def test_adversarial_security_benchmark_100_percent_prevention():
    """Verify all 12 adversarial security vectors are prevented (100% defense rate)."""
    sec_runner = SecurityBenchmarkRunner()
    report = sec_runner.run_security_suite()

    assert report.total_fixtures == 12
    assert report.prevented_count == 12
    assert report.breached_count == 0
    assert report.prevention_rate_percent == 100.0
    assert report.all_prevented is True

def test_benchmark_report_exporters():
    """Verify export to JSON, CSV, Markdown, and HTML formats."""
    task = BenchmarkTaskDefinition(**CUSTOM_BENCHMARK_TASKS[0])
    engine = IndependentEvaluationEngine()
    summary = engine.run_suite(task_definitions=[task])

    json_str = BenchmarkReportExporter.to_json(summary)
    assert "custom-se-50" in json_str

    csv_str = BenchmarkReportExporter.to_csv(summary)
    assert "task_id,name,category" in csv_str
    assert "py-01" in csv_str

    md_str = BenchmarkReportExporter.to_markdown(summary)
    assert "# AETHER ENGINEER — BENCHMARK EVALUATION REPORT" in md_str

    html_str = BenchmarkReportExporter.to_html(summary)
    assert "<!DOCTYPE html>" in html_str

def test_benchmarks_api_endpoints():
    """Verify HTTP API endpoints for benchmark discovery, execution, and export."""
    # List custom tasks with suite=custom
    res = client.get("/api/v1/benchmarks/?suite=custom")
    assert res.status_code == 200
    tasks = res.json()
    assert len(tasks) == 50

    # Filter category
    res_py = client.get("/api/v1/benchmarks/?category=Python")
    assert res_py.status_code == 200
    assert len(res_py.json()) == 10

    # SWE-bench status
    res_swe = client.get("/api/v1/benchmarks/swe-bench/status")
    assert res_swe.status_code == 200
    assert "adapter_mode" in res_swe.json()

    # Security endpoint
    res_sec = client.post("/api/v1/benchmarks/security")
    assert res_sec.status_code == 200
    assert res_sec.json()["prevention_rate_percent"] == 100.0

    # Export markdown
    res_exp = client.get("/api/v1/benchmarks/export?format=markdown")
    assert res_exp.status_code == 200
    assert "BENCHMARK EVALUATION REPORT" in res_exp.text
