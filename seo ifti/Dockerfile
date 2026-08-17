# ==============================================================================
# GitHub Developer Advocate AI Agent - Production Cloud Run Dockerfile
# Base: Python 3.11-slim (Optimized for minimal image size & ultra-fast cold starts)
# ==============================================================================

FROM python:3.11-slim AS runtime

# Set Python environment variables for container optimization
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080 \
    APP_HOME=/app

WORKDIR $APP_HOME

# Install security updates & essential runtime certificates
RUN apt-get update && \
    apt-get install -y --no-install-recommends ca-certificates curl && \
    rm -rf /var/lib/apt/lists/*

# Create a non-root system user and group for hardened security
RUN addgroup --system --gid 1001 appgroup && \
    adduser --system --uid 1001 --gid 1001 --no-create-home appuser

# Copy and install dependencies in a dedicated layer to leverage Docker build cache
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY . .

# Set ownership and permissions to non-root user
RUN mkdir -p media_storage && \
    chown -R appuser:appgroup $APP_HOME && \
    chmod -R 775 $APP_HOME

# Switch to non-root execution
USER appuser

# Expose default Cloud Run container port
EXPOSE 8080

# Healthcheck for container readiness (Cloud Run uses HTTP probes)
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT}/healthz || exit 1

# Start Uvicorn ASGI server binding dynamically to Cloud Run's $PORT
CMD ["sh", "-c", "exec uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080} --workers 1 --timeout-keep-alive 75 --access-log"]
