from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.models.task import Task
from backend.app.models.user import User
from backend.app.core.auth import get_current_user, verify_workspace_access
from backend.app.services.streaming.event_broadcaster import broadcaster

router = APIRouter()

@router.get("/stream/{task_id}")
async def stream_task_events(
    task_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Subscribes to live Server-Sent Events (SSE) for an active engineering task.
    Enforces workspace authorization and emits real progress events and heartbeats.
    """
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found.")

    if task.workspace:
        verify_workspace_access(task.workspace, current_user)

    subscriber_queue = broadcaster.subscribe(task_id)

    return StreamingResponse(
        broadcaster.event_generator(task_id, subscriber_queue),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

