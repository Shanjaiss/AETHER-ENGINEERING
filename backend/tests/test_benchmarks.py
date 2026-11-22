import pytest
from backend.app.services.evaluation.benchmark_suite import BENCHMARK_TASKS
from backend.app.services.evaluation.benchmark_runner import BenchmarkRunner

def test_benchmark_suite_definitions():
    assert len(BENCHMARK_TASKS) == 20
    categories = {b["category"] for b in BENCHMARK_TASKS}
    assert "Bug Fixing" in categories
    assert "Unit-Test Generation" in categories
    assert "Endpoint Implementation" in categories
    assert "Refactoring" in categories
    assert "TypeScript Errors" in categories
    assert "Python Exceptions" in categories
    assert "Validation Failures" in categories
    assert "Dependency Issues" in categories
    assert "Authentication Defects" in categories
    assert "Frontend Bugs" in categories

def test_list_benchmarks_api(client):
    res = client.get("/api/v1/benchmarks/")
    assert res.status_code == 200
    benchmarks = res.json()
    assert len(benchmarks) == 20
    assert benchmarks[0]["id"] == "bench-01"
    assert "expected_files" in benchmarks[0]

def test_run_benchmarks_execution(client, db_session):
    # Run a subset of benchmarks to verify real execution and honest scoring
    payload = {
        "benchmark_ids": ["bench-01", "bench-02", "bench-05", "bench-11", "bench-17"]
    }
    res = client.post("/api/v1/benchmarks/run", json=payload)
    assert res.status_code == 200
    report = res.json()

    assert report["total_benchmarks_run"] == 5
    assert report["verified_pass_rate_percent"] == 100.0
    assert report["avg_duration_seconds"] > 0
    assert report["total_security_violations"] == 0
    assert "Apple Silicon M1" in report["environment"]

    # Verify category breakdown
    assert "Bug Fixing" in report["category_breakdown"]
    assert report["category_breakdown"]["Bug Fixing"]["passed"] == 2

    # Verify historical runs endpoint
    hist_res = client.get("/api/v1/benchmarks/runs")
    assert hist_res.status_code == 200
    runs = hist_res.json()
    assert len(runs) >= 5
    assert runs[0]["test_passed"] is True

