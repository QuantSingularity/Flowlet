# ---- Build Stage ----
FROM python:3.11-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt ./requirements.txt
RUN pip install --upgrade pip && \
    pip install --prefix=/install --no-cache-dir -r requirements.txt

# ---- Runtime Stage ----
FROM python:3.11-slim AS runtime

WORKDIR /app

# Install runtime-only system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Create non-root user for security
RUN groupadd -r appgroup && useradd -r -g appgroup -d /app appuser

# Copy application code
COPY --chown=appuser:appgroup backend/ .
COPY --chown=appuser:appgroup ml_services ./ml_services

# Create required directories
RUN mkdir -p /app/database /app/logs /app/ml_models && \
    chown -R appuser:appgroup /app/database /app/logs /app/ml_models

USER appuser

# Environment defaults (should be overridden in production)
ENV FLASK_CONFIG=production \
    FLASK_ENV=production \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=5000 \
    ML_MODEL_DIR=/app/ml_models

EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:${PORT}/api/v1/monitoring/health || exit 1

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "--worker-class", "sync", \
     "--timeout", "120", "--keep-alive", "5", "--max-requests", "1000", \
     "--max-requests-jitter", "100", "--access-logfile", "-", "--error-logfile", "-", \
     "run_server:app"]
