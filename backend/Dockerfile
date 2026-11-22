# Multi-stage production Dockerfile for AETHER ENGINEER Backend
# Target platform: linux/arm64 (Apple Silicon M1 compatible) and linux/amd64

# Stage 1: Build & wheels cache
FROM python:3.12-slim-bookworm AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Stage 2: Minimal unprivileged production runtime
FROM python:3.12-slim-bookworm AS runner

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/home/aether/.local/bin:$PATH" \
    PORT=8000 \
    APP_ENV=production

# Install curl for container health check
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Create unprivileged system group and user
RUN groupadd -g 10001 aether && \
    useradd -u 10001 -g aether -s /bin/bash -m aether

WORKDIR /app

# Copy installed site-packages from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy backend source code and migrations
COPY --chown=aether:aether backend /app/backend
COPY --chown=aether:aether alembic.ini /app/alembic.ini

# Create workspaces directory with appropriate non-root ownership
RUN mkdir -p /app/workspaces && chown -R aether:aether /app/workspaces

USER aether

EXPOSE 8000

# Container healthcheck against FastAPI health endpoint
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

ENTRYPOINT ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]

