"""Escalation handling routes"""
from __future__ import annotations
from fastapi import APIRouter
from pydantic import BaseModel
from services.escalation_service import escalation_service
from core.utils import generate_id, get_logger

logger = get_logger(__name__)
router = APIRouter(tags=["escalation"])

class EscalationRequest(BaseModel):
    session_id: str
    reason: str
    severity: str = "high_risk"

@router.post("/escalate")
async def escalate_case(request: EscalationRequest):
    escalation_id = generate_id("ESC")
    await escalation_service.trigger(
        escalation_id=escalation_id,
        session_id=request.session_id,
        reason=request.reason,
        severity=request.severity
    )
    logger.warning(f"Case escalated: {escalation_id}")
    return {"success": True, "escalation_id": escalation_id}
