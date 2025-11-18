import os

# Gunicorn config variables
loglevel = os.environ.get("LOG_LEVEL", "info")
workers = int(os.environ.get("GUNICORN_WORKERS", "4"))
bind = os.environ.get("GUNICORN_BIND", "0.0.0.0:80")
worker_class = os.environ.get("GUNICORN_WORKER_CLASS", "uvicorn.workers.UvicornWorker")
timeout = int(os.environ.get("GUNICORN_TIMEOUT", "120"))
keepalive = int(os.environ.get("GUNICORN_KEEPALIVE", "5"))
