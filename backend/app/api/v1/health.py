from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from backend.app.core.config import settings
from backend.app.core.database import get_db
from backend.app.schemas.health import HealthResponse

router = APIRouter()

@router.get("/health", response_model=HealthResponse, summary="System Health and Readiness")
def check_health(db: Session = Depends(get_db)):
    """Health endpoint returning database, LLM provider, and system readiness status."""
    db_ok = False
    try:
        db.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        db_ok = False

    llm_configured = (
        settings.LLM_PROVIDER != "unconfigured" and (
            (settings.LLM_PROVIDER == "openai" and bool(settings.OPENAI_API_KEY)) or
            (settings.LLM_PROVIDER == "anthropic" and bool(settings.ANTHROPIC_API_KEY)) or
            (settings.LLM_PROVIDER == "gemini" and bool(settings.GEMINI_API_KEY)) or
            (settings.LLM_PROVIDER == "ollama" and bool(settings.OLLAMA_BASE_URL))
        )
    )

    return HealthResponse(
        status="healthy" if db_ok else "degraded",
        version=settings.APP_VERSION,
        environment=settings.APP_ENV,
        database_connected=db_ok,
        llm_configured=llm_configured,
        llm_provider=settings.LLM_PROVIDER,
        details={
            "debug": settings.DEBUG,
            "workspace_root": str(settings.resolved_workspace_root),
            "max_repair_attempts": settings.MAX_REPAIR_ATTEMPTS,
            "max_parallel_tasks": settings.MAX_PARALLEL_TASKS,
        }
    )

