"""Safety classification service"""
from __future__ import annotations
from core.settings import CRITICAL_KEYWORDS, HIGH_RISK_KEYWORDS
from core.config import settings
from core.utils import get_logger

logger = get_logger(__name__)

class SafetyService:
    async def check_input(self, text: str) -> dict:
        text_lower = text.lower()
        if any(kw in text_lower for kw in CRITICAL_KEYWORDS):
            return {"level": "critical", "score": 0.95, "should_escalate": True}
        if any(kw in text_lower for kw in HIGH_RISK_KEYWORDS):
            return {"level": "high_risk", "score": 0.75, "should_escalate": False}
        return {"level": "safe", "score": 0.1, "should_escalate": False}
    
    async def check_output(self, text: str) -> dict:
        return {"level": "safe", "score": 0.1, "should_escalate": False}

safety_service = SafetyService()
