from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.models.task import Task
from backend.app.models.user import User
from backend.app.core.auth import get_current_user, verify_workspace_access
from backend.app.services.queue.task_queue import TaskQueueManager, TaskJob, JobStatus

router = APIRouter()

class EnqueueTaskRequest(BaseModel):
    task_id: str
    task_type: str = "EXECUTE_LIFECYCLE"
    idempotency_key: Optional[str] = None
    payload: Dict[str, Any] = {}

@router.post("/enqueue", status_code=status.HTTP_202_ACCEPTED)
def enqueue_task(
    req: EnqueueTaskRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Submits an engineering task to the asynchronous background processing queue."""
    task = db.query(Task).filter(Task.id == req.task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail=f"Task '{req.task_id}' not found.")

    if task.workspace:
        verify_workspace_access(task.workspace, current_user)

    queue = TaskQueueManager.get_queue()
    job = TaskJob(
        task_id=task.id,
        tenant_id=current_user.tenant_id if current_user else "default-tenant",
        task_type=req.task_type,
        idempotency_key=req.idempotency_key,
        payload=req.payload
    )
    enqueued_job = queue.enqueue(job)
    return {
        "job_id": enqueued_job.job_id,
        "task_id": enqueued_job.task_id,
        "status": enqueued_job.status.value,
        "queue_depth": queue.get_queue_depth(),
        "created_at": enqueued_job.created_at
    }

@router.get("/status/{job_id}")
def get_job_status(job_id: str):
    """Retrieves asynchronous job state, progress percentage, and retry count."""
    queue = TaskQueueManager.get_queue()
    job = queue.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found.")
    return {
        "job_id": job.job_id,
        "task_id": job.task_id,
        "status": job.status.value,
        "progress_pct": job.progress_pct,
        "current_step": job.current_step,
        "retry_count": job.retry_count,
        "error_message": job.error_message,
        "result": job.result
    }

@router.post("/cancel/{job_id}")
def cancel_job(job_id: str):
    """Cancels a queued or in-flight background job."""
    queue = TaskQueueManager.get_queue()
    success = queue.cancel_job(job_id)
    if not success:
        raise HTTPException(status_code=400, detail=f"Could not cancel job '{job_id}'. It may already be completed.")
    return {"message": f"Job '{job_id}' cancelled successfully."}

@router.get("/stats")
def get_queue_stats():
    """Returns queue depth and throughput statistics."""
    queue = TaskQueueManager.get_queue()
    return {
        "queue_depth": queue.get_queue_depth(),
        "backend": queue.__class__.__name__
    }

