#!/bin/bash
set -e
export PYTHONPATH=.
export PATH="/opt/homebrew/bin:$PATH"

echo "=== Running Backend Tests (pytest) ==="
.venv/bin/pytest -v backend/tests

echo "=== Running Frontend Tests (vitest) ==="
npm run test --prefix frontend

echo "=== Building Frontend (typecheck + vite) ==="
npm run build --prefix frontend

echo "=== ALL CHECKS PASSED ==="

