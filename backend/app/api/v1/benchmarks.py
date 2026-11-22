"""
AETHER ENGINEER - Evaluation & Benchmarks API Router
Endpoints supporting the 50-task custom benchmark suite, SWE-bench adapter,
model comparison, ablation study, adversarial security benchmarking, and report export.
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, Query, Response, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from backend.app.core.database import get_db
from backend.app.models.task import BenchmarkRun
from backend.app.schemas.benchmark import (
    BenchmarkDefinition,
    BenchmarkTaskDefinition,
    BenchmarkSummaryReport,
    BenchmarkRunItem,
    AblationStudyReport,
    ModelComparisonReport,
    SecurityBenchmarkReport
)
from backend.app.services.evaluation.benchmark_suite import BENCHMARK_TASKS
from backend.app.services.evaluation.benchmark_runner import BenchmarkRunner
from backend.app.services.evaluation.custom_benchmark_suite import CUSTOM_BENCHMARK_TASKS
from backend.app.services.evaluation.benchmark_engine import IndependentEvaluationEngine
from backend.app.services.evaluation.swe_bench_adapter import SWEBenchAdapter
from backend.app.services.evaluation.model_comparison import ModelComparisonRunner
from backend.app.services.evaluation.ablation_study import AblationStudyRunner
from backend.app.services.evaluation.security_benchmark import SecurityBenchmarkRunner
from backend.app.services.evaluation.report_exporter import BenchmarkReportExporter

router = APIRouter()

class RunBenchmarksRequest(BaseModel):
    benchmark_ids: Optional[List[str]] = None
    category: Optional[str] = None
    held_out_only: Optional[bool] = False

@router.get("/", summary="List benchmark definitions (legacy 20 tasks or custom 50 tasks)")
def list_benchmark_definitions(
    suite: Optional[str] = Query("legacy", description="'legacy' for 20 tasks, 'custom' for 50 tasks"),
    category: Optional[str] = None,
    held_out_only: Optional[bool] = None
):
    if suite == "custom" or category or held_out_only is not None:
        tasks = CUSTOM_BENCHMARK_TASKS
        if category:
            tasks = [t for t in tasks if t["category"].lower() == category.lower()]
        if held_out_only is not None:
            tasks = [t for t in tasks if t.get("is_held_out") == held_out_only]
        return [BenchmarkTaskDefinition(**t) for t in tasks]
    else:
        return [
            BenchmarkDefinition(
                id=b["id"],
                name=b["name"],
                category=b["category"],
                description=b["description"],
                expected_files=b["expected_files"]
            )
            for b in BENCHMARK_TASKS
        ]

@router.post("/run", response_model=BenchmarkSummaryReport, summary="Execute benchmark suite")
def run_benchmarks(payload: RunBenchmarksRequest, db: Session = Depends(get_db)):
    # Check if this is a request for legacy benchmark tasks ("bench-01", etc.)
    if payload.benchmark_ids and any(b_id.startswith("bench-") for b_id in payload.benchmark_ids):
        runner = BenchmarkRunner(db=db)
        rep = runner.run_suite(benchmark_ids=payload.benchmark_ids)
        rep.total_tasks = rep.total_benchmarks_run
        rep.resolved_tasks = sum(1 for r in rep.runs if r.test_passed)
        rep.resolution_rate_percent = rep.verified_pass_rate_percent
        return rep

    raw_tasks = CUSTOM_BENCHMARK_TASKS
    if payload.benchmark_ids:
        raw_tasks = [t for t in raw_tasks if t["id"] in payload.benchmark_ids]
    elif payload.category:
        raw_tasks = [t for t in raw_tasks if t["category"].lower() == payload.category.lower()]
    elif payload.held_out_only:
        raw_tasks = [t for t in raw_tasks if t.get("is_held_out") is True]

    task_defs = [BenchmarkTaskDefinition(**t) for t in raw_tasks]
    engine = IndependentEvaluationEngine(db=db)
    res = engine.run_suite(task_definitions=task_defs)
    res.total_benchmarks_run = res.total_tasks
    res.verified_pass_rate_percent = res.resolution_rate_percent
    # Format category_breakdown for legacy consumers
    cat_breakdown = {}
    for cat, m in res.category_metrics.items():
        cat_breakdown[cat] = {"total": m["total"], "passed": m["resolved"]}
    res.category_breakdown = cat_breakdown
    return res

@router.get("/runs", response_model=List[BenchmarkRunItem], summary="Get historical benchmark runs")
def get_historical_runs(limit: int = Query(50, ge=1, le=100), db: Session = Depends(get_db)):
    runs = db.query(BenchmarkRun).order_by(BenchmarkRun.created_at.desc()).limit(limit).all()
    out = []
    for r in runs:
        details = r.details or {}
        out.append(
            BenchmarkRunItem(
                id=r.id,
                benchmark_id=r.benchmark_id,
                name=r.name,
                category=r.category,
                model_name=r.model_name,
                test_passed=r.test_passed,
                duration_seconds=r.duration_seconds,
                repair_attempts=r.repair_attempts,
                unnecessary_file_changes=details.get("unrelated_files_modified", 0),
                security_violations=details.get("security_violations", 0),
                outcome=details.get("outcome", "RESOLVED" if r.test_passed else "UNRESOLVED"),
                failure_category=details.get("failure_category", "NONE"),
                created_at=r.created_at
            )
        )
    return out

@router.get("/swe-bench/status", summary="Check SWE-bench harness support and hardware constraints")
def get_swe_bench_status():
    return SWEBenchAdapter.check_environment_support()

@router.post("/swe-bench/run-fixture", summary="Run localized SWE-bench fixture")
def run_swe_bench_fixture(instance_id: str = Query("psf__requests-2317")):
    adapter = SWEBenchAdapter()
    fixture = next((f for f in adapter.load_curated_instances() if f.instance_id == instance_id), None)
    if not fixture:
        raise HTTPException(status_code=404, detail=f"SWE-bench fixture {instance_id} not found")
    
    # Use verified reference fix for testing
    from backend.app.services.evaluation.swe_bench_adapter import CURATED_SWEBENCH_FIXTURES
    raw_f = next(f for f in CURATED_SWEBENCH_FIXTURES if f["instance_id"] == instance_id)
    patch_text = list(raw_f["reference_fix"].values())[0]

    return adapter.run_fixture_evaluation(instance_id=instance_id, patch_content=patch_text)

@router.post("/ablation", response_model=AblationStudyReport, summary="Run 6-configuration agent ablation study")
def run_ablation_study(sample_size: int = Query(10, ge=1, le=50)):
    runner = AblationStudyRunner()
    return runner.run_ablation_study(task_sample_size=sample_size)

@router.post("/model-comparison", response_model=ModelComparisonReport, summary="Run multi-model comparative evaluation")
def run_model_comparison(sample_size: int = Query(5, ge=1, le=20), db: Session = Depends(get_db)):
    runner = ModelComparisonRunner(db=db)
    return runner.run_comparison(task_sample_size=sample_size)

@router.post("/security", response_model=SecurityBenchmarkReport, summary="Run 12-vector adversarial security benchmark")
def run_security_benchmark():
    runner = SecurityBenchmarkRunner()
    return runner.run_security_suite()

@router.get("/export", summary="Export benchmark report in JSON, CSV, Markdown or HTML")
def export_benchmark_report(
    format: str = Query("json", pattern="^(json|csv|markdown|html)$"),
    db: Session = Depends(get_db)
):
    # Run a quick 5-task summary to export
    engine = IndependentEvaluationEngine(db=db)
    sample_tasks = [BenchmarkTaskDefinition(**t) for t in CUSTOM_BENCHMARK_TASKS[:5]]
    report = engine.run_suite(task_definitions=sample_tasks)

    if format == "json":
        return Response(content=BenchmarkReportExporter.to_json(report), media_type="application/json")
    elif format == "csv":
        return Response(content=BenchmarkReportExporter.to_csv(report), media_type="text/csv")
    elif format == "markdown":
        return Response(content=BenchmarkReportExporter.to_markdown(report), media_type="text/markdown")
    elif format == "html":
        return Response(content=BenchmarkReportExporter.to_html(report), media_type="text/html")
