import time
import uuid
import threading
from typing import Dict, Any, Optional, List
from enum import Enum
from pydantic import BaseModel, Field

class JobStatus(str, Enum):
    QUEUED = "QUEUED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"

class TaskJob(BaseModel):
    job_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    task_id: str
    tenant_id: str = "default-tenant"
    task_type: str = "GENERAL"
    payload: Dict[str, Any] = Field(default_factory=dict)
    status: JobStatus = JobStatus.QUEUED
    progress_pct: int = 0
    current_step: str = "QUEUED"
    retry_count: int = 0
    max_retries: int = 3
    idempotency_key: Optional[str] = None
    error_message: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    created_at: float = Field(default_factory=time.time)
    updated_at: float = Field(default_factory=time.time)

class BaseTaskQueue:
    """Abstract interface for task queues (in-memory or Redis)."""
    def enqueue(self, job: TaskJob) -> TaskJob:
        raise NotImplementedError

    def get_job(self, job_id: str) -> Optional[TaskJob]:
        raise NotImplementedError

    def get_job_by_task_id(self, task_id: str) -> Optional[TaskJob]:
        raise NotImplementedError

    def cancel_job(self, job_id: str) -> bool:
        raise NotImplementedError

    def dequeue(self) -> Optional[TaskJob]:
        raise NotImplementedError

    def update_job(self, job: TaskJob) -> None:
        raise NotImplementedError

    def get_queue_depth(self) -> int:
        raise NotImplementedError

class InMemoryTaskQueue(BaseTaskQueue):
    """Thread-safe in-memory task queue with idempotency and retry tracking."""
    def __init__(self):
        self._lock = threading.Lock()
        self._jobs: Dict[str, TaskJob] = {}
        self._queue: List[str] = []
        self._idempotency_map: Dict[str, str] = {}  # idempotency_key -> job_id

    def enqueue(self, job: TaskJob) -> TaskJob:
        with self._lock:
            # Idempotency check: if duplicate action submitted with same key, return existing job
            if job.idempotency_key and job.idempotency_key in self._idempotency_map:
                existing_id = self._idempotency_map[job.idempotency_key]
                if existing_id in self._jobs:
                    return self._jobs[existing_id]

            self._jobs[job.job_id] = job
            self._queue.append(job.job_id)
            if job.idempotency_key:
                self._idempotency_map[job.idempotency_key] = job.job_id
            return job

    def get_job(self, job_id: str) -> Optional[TaskJob]:
        with self._lock:
            return self._jobs.get(job_id)

    def get_job_by_task_id(self, task_id: str) -> Optional[TaskJob]:
        with self._lock:
            for j in self._jobs.values():
                if j.task_id == task_id:
                    return j
            return None

    def cancel_job(self, job_id: str) -> bool:
        with self._lock:
            if job_id in self._jobs:
                job = self._jobs[job_id]
                if job.status in (JobStatus.QUEUED, JobStatus.PROCESSING):
                    job.status = JobStatus.CANCELLED
                    job.updated_at = time.time()
                    if job_id in self._queue:
                        self._queue.remove(job_id)
                    return True
            return False

    def dequeue(self) -> Optional[TaskJob]:
        with self._lock:
            while self._queue:
                job_id = self._queue.pop(0)
                job = self._jobs.get(job_id)
                if job and job.status == JobStatus.QUEUED:
                    job.status = JobStatus.PROCESSING
                    job.updated_at = time.time()
                    return job
            return None

    def update_job(self, job: TaskJob) -> None:
        with self._lock:
            job.updated_at = time.time()
            self._jobs[job.job_id] = job

    def get_queue_depth(self) -> int:
        with self._lock:
            return len(self._queue)

class TaskQueueManager:
    _instance: Optional[BaseTaskQueue] = None

    @classmethod
    def get_queue(cls) -> BaseTaskQueue:
        if cls._instance is None:
            # By default on Apple Silicon Mac M1, instantiate thread-safe in-memory queue
            cls._instance = InMemoryTaskQueue()
        return cls._instance

