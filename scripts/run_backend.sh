#!/bin/bash
set -e
export PYTHONPATH=.
.venv/bin/uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload

