# --- Stage 1: Build dependencies ---
FROM python:3.11-slim as builder

WORKDIR /app

# Install poetry
RUN pip install poetry

# Copy dependency definition files
COPY poetry.lock pyproject.toml ./

# Install dependencies into a virtual environment
RUN poetry config virtualenvs.in-project true && \
    poetry install --no-dev --no-root


# --- Stage 2: Final application image ---
FROM python:3.11-slim as final

# Create a non-root user
RUN useradd --create-home appuser
WORKDIR /home/appuser/app

# Copy the virtual environment from the builder stage
COPY --from=builder /app/.venv ./.venv

# Copy the application source code and configuration
COPY --chown=appuser:appuser . .

# Activate the virtual environment
ENV PATH="/home/appuser/app/.venv/bin:$PATH"

# Switch to the non-root user
USER appuser

# Expose the port the app runs on
EXPOSE 80

# Command to run the application
CMD ["gunicorn", "-c", "gunicorn_conf.py", "main:app"]
