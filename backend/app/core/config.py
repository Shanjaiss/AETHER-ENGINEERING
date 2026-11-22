from pathlib import Path
from typing import List, Union
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
import json

class Settings(BaseSettings):
    """Application configuration loaded from environment and defaults."""
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    APP_NAME: str = "AETHER ENGINEER"
    APP_VERSION: str = "1.0.0-rc.1"
    APP_ENV: str = "development"
    DEBUG: bool = True
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    CORS_ORIGINS: Union[List[str], str] = ["http://localhost:5173", "http://127.0.0.1:5173"]
    LOG_LEVEL: str = "INFO"

    # Database
    DATABASE_URL: str = "sqlite:///./aether_engineer.db"

    # Security & Workspaces
    WORKSPACE_ROOT: str = "./workspaces"
    ALLOWED_REPO_ROOTS: Union[List[str], str] = [
        "/Users/shanjaisenthil/Documents",
        "/Users/shanjaisenthil/Projects"
    ]
    ISOLATED_SANDBOX_TIMEOUT_SECONDS: int = 60
    MAX_REPAIR_ATTEMPTS: int = 3
    MAX_PARALLEL_TASKS: int = 2

    # LLM Settings
    LLM_PROVIDER: str = "unconfigured"  # unconfigured | openai | anthropic | gemini | ollama
    LLM_MODEL: str = ""
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    GEMINI_API_KEY: str = ""
    OLLAMA_BASE_URL: str = "http://127.0.0.1:11434"

    @field_validator("CORS_ORIGINS", "ALLOWED_REPO_ROOTS", mode="before")
    @classmethod
    def parse_json_or_list(cls, value):
        if isinstance(value, str):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @property
    def resolved_workspace_root(self) -> Path:
        path = Path(self.WORKSPACE_ROOT).resolve()
        path.mkdir(parents=True, exist_ok=True)
        return path

settings = Settings()

