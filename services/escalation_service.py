"""Clinician escalation service"""
from __future__ import annotations
from core.utils import get_logger

logger = get_logger(__name__)

class EscalationService:
    async def trigger(self, escalation_id: str, session_id: str, reason: str, severity: str):
        logger.warning(f"ESCALATION {escalation_id}: {severity} - {reason}")

escalation_service = EscalationService()
