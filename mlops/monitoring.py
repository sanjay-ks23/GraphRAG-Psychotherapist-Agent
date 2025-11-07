"""Prometheus metrics exporter"""
from __future__ import annotations
from fastapi import APIRouter
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response

router = APIRouter(tags=["metrics"])

request_count = Counter("sahyog_requests_total", "Total requests")
request_latency = Histogram("sahyog_request_duration_seconds", "Request duration")

@router.get("/metrics")
async def metrics():
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
