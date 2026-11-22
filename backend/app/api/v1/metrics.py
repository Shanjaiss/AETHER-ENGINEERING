from fastapi import APIRouter, Response
from backend.app.core.metrics import metrics

router = APIRouter()

@router.get("/metrics")
def get_prometheus_metrics():
    """Exposes application and infrastructure metrics in Prometheus text exposition format."""
    content = metrics.generate_prometheus_output()
    return Response(content=content, media_type="text/plain; version=0.0.4; charset=utf-8")

