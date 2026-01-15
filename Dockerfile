FROM python:3.11-slim AS builder

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.11-slim

# Create non-root user
RUN useradd --create-home appuser
WORKDIR /app

# Install runtime deps
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

# Copy Python packages
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy app code
COPY --chown=appuser:appuser . .

USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

EXPOSE 8000 7860

CMD ["gunicorn", "main:app", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:8000", "-w", "2"]
