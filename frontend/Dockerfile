# Multi-stage production Dockerfile for AETHER ENGINEER Frontend
# Stage 1: Build Vite / React application
FROM node:22-alpine AS builder

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm ci --prefer-offline --no-audit

COPY . .
RUN npm run build

# Stage 2: Serve static production assets with unprivileged Nginx
FROM nginxinc/nginx-unprivileged:alpine-slim AS runner

USER nginx

# Copy custom nginx configuration for SPA routing
COPY --chown=nginx:nginx <<EOF /etc/nginx/conf.d/default.conf
server {
    listen 8080;
    server_name localhost;

    root /usr/share/nginx/html;
    index index.html;

    # Security headers
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Content-Security-Policy "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self' http://localhost:8000 http://127.0.0.1:8000 ws: wss:;" always;

    # Gzip compression
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;

    # Cache static assets
    location /assets/ {
        expires 1y;
        add_header Cache-Control "public, no-transform, immutable";
    }

    # SPA routing fallback
    location / {
        try_files \$uri \$uri/ /index.html;
    }

    # Health check
    location /healthz {
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }
}
EOF

# Copy compiled static assets from builder stage
COPY --from=builder --chown=nginx:nginx /app/dist /usr/share/nginx/html

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD wget -q -O - http://localhost:8080/healthz || exit 1

CMD ["nginx", "-g", "daemon off;"]

