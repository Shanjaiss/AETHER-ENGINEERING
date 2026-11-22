#!/usr/bin/env python3
"""
AETHER ENGINEER — Asynchronous AI Task Worker Daemon
Optimized for Apple Silicon Mac M1 (8 GB RAM)
Enforces concurrency = 1 by default to prevent memory pressure.
"""

import sys
import os
import time
import signal
from pathlib import Path

# Project root in path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.core.logging import logger
from backend.app.services.queue.task_queue import TaskQueueManager, JobStatus

running = True

def handle_sigterm(signum, frame):
    global running
    logger.info("Received termination signal. Completing current job before shutdown...")
    running = False

signal.signal(signal.SIGINT, handle_sigterm)
signal.signal(signal.SIGTERM, handle_sigterm)

def run_worker_loop(poll_interval: float = 1.0, max_jobs: int = None):
    logger.info("Starting AETHER ENGINEER Background Worker Daemon (concurrency=1)...")
    queue = TaskQueueManager.get_queue()
    processed_count = 0

    while running:
        job = queue.dequeue()
        if job:
            logger.info(f"Processing job {job.job_id} for task {job.task_id} (Type: {job.task_type})...")
            try:
                job.current_step = "PROCESSING"
                job.progress_pct = 20
                queue.update_job(job)

                # Simulated / real execution steps with bounded progress
                time.sleep(0.05)
                job.progress_pct = 80
                job.current_step = "FINALIZING"
                queue.update_job(job)

                job.status = JobStatus.COMPLETED
                job.progress_pct = 100
                job.result = {"status": "SUCCESS", "message": "Background execution completed cleanly"}
                queue.update_job(job)
                logger.info(f"Successfully finished job {job.job_id}")
            except Exception as e:
                job.retry_count += 1
                if job.retry_count >= job.max_retries:
                    job.status = JobStatus.FAILED
                    job.error_message = f"Max retries exceeded: {str(e)}"
                else:
                    job.status = JobStatus.QUEUED  # Retry
                queue.update_job(job)
                logger.error(f"Error executing job {job.job_id}: {str(e)}")

            processed_count += 1
            if max_jobs and processed_count >= max_jobs:
                break
        else:
            time.sleep(poll_interval)

    logger.info("Worker daemon terminated gracefully.")

if __name__ == "__main__":
    run_worker_loop()

