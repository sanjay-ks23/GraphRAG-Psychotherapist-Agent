"""Provenance tracking service"""
from __future__ import annotations
from core.utils import get_logger

logger = get_logger(__name__)

class ProvenanceService:
    async def track(self, session_id: str, sources: list):
        logger.info(f"Tracked {len(sources)} sources for {session_id}")

provenance_service = ProvenanceService()
