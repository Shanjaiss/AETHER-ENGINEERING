from fastapi import APIRouter
from backend.app.api.v1.health import router as health_router
from backend.app.api.v1.workspaces import router as workspaces_router
from backend.app.api.v1.tasks import router as tasks_router
from backend.app.api.v1.repositories import router as repositories_router
from backend.app.api.v1.planning import router as planning_router
from backend.app.api.v1.coding import router as coding_router
from backend.app.api.v1.verification import router as verification_router
from backend.app.api.v1.review import router as review_router
from backend.app.api.v1.benchmarks import router as benchmarks_router
from backend.app.api.v1.settings import router as settings_router
from backend.app.api.v1.auth import router as auth_router
from backend.app.api.v1.events import router as events_router
from backend.app.api.v1.metrics import router as metrics_router
from backend.app.api.v1.queue import router as queue_router

api_router = APIRouter()

api_router.include_router(health_router, prefix="", tags=["health"])
api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(workspaces_router, prefix="/workspaces", tags=["workspaces"])
api_router.include_router(tasks_router, prefix="/tasks", tags=["tasks"])
api_router.include_router(repositories_router, prefix="/repositories", tags=["repositories"])
api_router.include_router(planning_router, prefix="/planning", tags=["planning"])
api_router.include_router(coding_router, prefix="/coding", tags=["coding"])
api_router.include_router(verification_router, prefix="/verification", tags=["verification"])
api_router.include_router(review_router, prefix="/review", tags=["review"])
api_router.include_router(benchmarks_router, prefix="/benchmarks", tags=["benchmarks"])
api_router.include_router(settings_router, prefix="/settings", tags=["settings"])
api_router.include_router(events_router, prefix="/events", tags=["events"])
api_router.include_router(metrics_router, prefix="", tags=["metrics"])
api_router.include_router(queue_router, prefix="/queue", tags=["queue"])
