from celery import Celery
from graph_rag.settings import settings

celery_app = Celery(
    "tasks",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["graph_rag.tasks"]
)

celery_app.conf.update(
    task_track_started=True,
)
