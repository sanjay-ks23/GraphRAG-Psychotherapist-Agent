# --- Stage 1: Build dependencies ---
FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt ./

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt


# --- Stage 2: Final application image ---
FROM python:3.11-slim as final

# Create a non-root user
RUN useradd --create-home appuser
WORKDIR /home/appuser/app

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy the application source code
COPY --chown=appuser:appuser . .

# Switch to the non-root user
USER appuser

# Expose ports: 80 for FastAPI (via nginx), 7860 for Gradio
EXPOSE 80 7860

# Environment variable to switch between modes
ENV APP_MODE=api

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default command runs FastAPI with gunicorn
# Override with: docker run ... python gradio_app.py
CMD ["sh", "-c", "if [ \"$APP_MODE\" = 'gradio' ]; then python gradio_app.py; else gunicorn -c gunicorn_conf.py main:app; fi"]

