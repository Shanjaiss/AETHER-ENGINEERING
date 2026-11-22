import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.core.database import init_db
from backend.app.core.security import SecurityException
from backend.app.core.metrics import metrics
from backend.app.api.v1.api import api_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION} [{settings.APP_ENV}]")
    # Initialize DB tables
    init_db()
    logger.info("Database schema initialized successfully.")
    yield
    logger.info(f"Shutting down {settings.APP_NAME}.")

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Autonomous AI Software Engineering Platform - From Requirement to Verified Code",
    lifespan=lifespan
)

# CORS Configuration
origins = settings.CORS_ORIGINS if isinstance(settings.CORS_ORIGINS, list) else [settings.CORS_ORIGINS]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Metrics & Latency Middleware
@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start_time = time.perf_counter()
    response = await call_next(request)
    duration = time.perf_counter() - start_time
    path = request.url.path
    # Normalize paths to prevent metric explosion
    if path.startswith("/api/v1/tasks/"):
        path = "/api/v1/tasks/{id}"
    elif path.startswith("/api/v1/workspaces/"):
        path = "/api/v1/workspaces/{id}"
    metrics.record_request(request.method, path, response.status_code, duration)
    return response

# Exception Handlers
@app.exception_handler(SecurityException)
async def security_exception_handler(request: Request, exc: SecurityException):
    logger.warning(f"Security violation blocked: {exc.detail} on {request.url}")
    metrics.record_security_violation("path_traversal_or_command_blocked")
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": "SecurityViolation", "detail": exc.detail}
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception on {request.url}: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": "InternalServerError", "detail": "An unexpected server error occurred."}
    )

# Include API Router
app.include_router(api_router, prefix="/api/v1")

@app.get("/", tags=["root"])
def root():
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "tagline": "From Requirement to Verified Code",
        "docs": "/docs",
        "health": "/api/v1/health"
    }

