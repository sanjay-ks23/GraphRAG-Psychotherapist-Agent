"""MLflow tracking integration"""
from __future__ import annotations
import mlflow
from core.config import settings

mlflow.set_tracking_uri(settings.MLFLOW_TRACKING_URI)
mlflow.set_experiment("sahyog")

def log_metrics(metrics: dict):
    with mlflow.start_run():
        for key, value in metrics.items():
            mlflow.log_metric(key, value)
