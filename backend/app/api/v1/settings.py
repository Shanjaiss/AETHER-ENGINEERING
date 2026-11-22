from typing import Optional, List, Dict, Any
from fastapi import APIRouter
from pydantic import BaseModel, Field
from backend.app.core.config import settings

router = APIRouter()

class SettingsResponse(BaseModel):
    app_name: str
    app_version: str
    app_env: str
    llm_provider: str
    llm_model: str
    ollama_base_url: str
    has_openai_key: bool
    has_anthropic_key: bool
    has_gemini_key: bool
    allowed_repo_roots: List[str]
    isolated_sandbox_timeout_seconds: int
    max_repair_attempts: int

class UpdateSettingsRequest(BaseModel):
    llm_provider: Optional[str] = None
    llm_model: Optional[str] = None
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    gemini_api_key: Optional[str] = None
    ollama_base_url: Optional[str] = None

@router.get("/", response_model=SettingsResponse, summary="Get current system settings and provider status")
def get_settings():
    roots = settings.ALLOWED_REPO_ROOTS
    if isinstance(roots, str):
        roots = [roots]
    return SettingsResponse(
        app_name=settings.APP_NAME,
        app_version=settings.APP_VERSION,
        app_env=settings.APP_ENV,
        llm_provider=settings.LLM_PROVIDER,
        llm_model=settings.LLM_MODEL,
        ollama_base_url=settings.OLLAMA_BASE_URL,
        has_openai_key=bool(settings.OPENAI_API_KEY),
        has_anthropic_key=bool(settings.ANTHROPIC_API_KEY),
        has_gemini_key=bool(settings.GEMINI_API_KEY),
        allowed_repo_roots=list(roots),
        isolated_sandbox_timeout_seconds=settings.ISOLATED_SANDBOX_TIMEOUT_SECONDS,
        max_repair_attempts=settings.MAX_REPAIR_ATTEMPTS
    )

@router.post("/", response_model=SettingsResponse, summary="Update runtime provider and settings")
def update_settings(payload: UpdateSettingsRequest):
    if payload.llm_provider is not None:
        settings.LLM_PROVIDER = payload.llm_provider
    if payload.llm_model is not None:
        settings.LLM_MODEL = payload.llm_model
    if payload.openai_api_key is not None:
        settings.OPENAI_API_KEY = payload.openai_api_key
    if payload.anthropic_api_key is not None:
        settings.ANTHROPIC_API_KEY = payload.anthropic_api_key
    if payload.gemini_api_key is not None:
        settings.GEMINI_API_KEY = payload.gemini_api_key
    if payload.ollama_base_url is not None:
        settings.OLLAMA_BASE_URL = payload.ollama_base_url

    return get_settings()

