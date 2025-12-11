"""
Safety Service for Mental Wellness Support Agent.

Provides real-time safety guardrails including crisis keyword detection,
risk scoring, and appropriate response handling.
"""
import logging
import re
from typing import Tuple, List, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class RiskLevel(Enum):
    """Risk level classifications for user messages."""
    SAFE = "safe"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class SafetyResult:
    """Result of safety analysis."""
    risk_level: RiskLevel
    risk_score: float
    triggered_keywords: List[str]
    requires_escalation: bool
    safe_response: Optional[str]


# Crisis and risk keywords organized by severity
CRITICAL_KEYWORDS = [
    r"\bsuicide\b", r"\bsuicidal\b", r"\bkill myself\b", r"\bend my life\b",
    r"\bwant to die\b", r"\bdon'?t want to live\b", r"\bself[- ]?harm\b",
    r"\bcut myself\b", r"\bhurt myself\b", r"\boverdose\b",
]

HIGH_RISK_KEYWORDS = [
    r"\babuse\b", r"\babused\b", r"\bviolence\b", r"\bviolent\b",
    r"\bhopeless\b", r"\bno hope\b", r"\bworthless\b", r"\bno reason to live\b",
    r"\bgive up\b", r"\bgiving up\b", r"\bcan'?t go on\b",
]

MODERATE_RISK_KEYWORDS = [
    r"\bdepressed\b", r"\bdepression\b", r"\banxiety\b", r"\banxious\b",
    r"\bpanic attack\b", r"\bscared\b", r"\bterrified\b", r"\btrauma\b",
    r"\bptsd\b", r"\beating disorder\b", r"\banorexia\b", r"\bbulimia\b",
]

# Safe response templates for different risk levels
CRISIS_RESPONSE = """
I'm really concerned about what you've shared with me. Your safety is the top priority right now.

**Please reach out for immediate support:**
- 🆘 **Emergency Services**: 911 (US) or your local emergency number
- 📱 **988 Suicide & Crisis Lifeline**: Call or text 988 (US)
- 💬 **Crisis Text Line**: Text HOME to 741741

These services are available 24/7 and staffed by trained professionals who can help.

You're not alone, and there are people who care about you and want to help. Would you like me to provide more information about any of these resources?
"""

HIGH_RISK_RESPONSE = """
I hear you, and what you're going through sounds really difficult. I want to make sure you have access to the right support.

**Support resources available to you:**
- 📞 **SAMHSA Helpline**: 1-800-662-4357 (24/7, free, confidential)
- 🌐 **SAMHSA Treatment Locator**: findtreatment.gov
- 💬 **Crisis Text Line**: Text HOME to 741741

It's okay to reach out for help. Would you like to talk more about what you're experiencing?
"""


class SafetyService:
    """
    Service for analyzing messages and applying safety guardrails.
    """
    
    def __init__(self):
        # Compile regex patterns for efficiency
        self._critical_patterns = [re.compile(p, re.IGNORECASE) for p in CRITICAL_KEYWORDS]
        self._high_patterns = [re.compile(p, re.IGNORECASE) for p in HIGH_RISK_KEYWORDS]
        self._moderate_patterns = [re.compile(p, re.IGNORECASE) for p in MODERATE_RISK_KEYWORDS]
    
    def analyze_message(self, message: str) -> SafetyResult:
        """
        Analyze a message for safety concerns.
        
        Args:
            message: The user message to analyze
            
        Returns:
            SafetyResult with risk assessment
        """
        triggered = []
        risk_score = 0.0
        
        # Check critical keywords (highest priority)
        for pattern in self._critical_patterns:
            if pattern.search(message):
                triggered.append(pattern.pattern)
                risk_score = max(risk_score, 0.95)
        
        # Check high-risk keywords
        for pattern in self._high_patterns:
            if pattern.search(message):
                triggered.append(pattern.pattern)
                risk_score = max(risk_score, 0.75)
        
        # Check moderate-risk keywords
        for pattern in self._moderate_patterns:
            if pattern.search(message):
                triggered.append(pattern.pattern)
                risk_score = max(risk_score, 0.5)
        
        # Determine risk level
        if risk_score >= 0.9:
            risk_level = RiskLevel.CRITICAL
            safe_response = CRISIS_RESPONSE
            requires_escalation = True
        elif risk_score >= 0.7:
            risk_level = RiskLevel.HIGH
            safe_response = HIGH_RISK_RESPONSE
            requires_escalation = True
        elif risk_score >= 0.4:
            risk_level = RiskLevel.MODERATE
            safe_response = None
            requires_escalation = False
        elif risk_score > 0:
            risk_level = RiskLevel.LOW
            safe_response = None
            requires_escalation = False
        else:
            risk_level = RiskLevel.SAFE
            safe_response = None
            requires_escalation = False
        
        logger.info(f"Safety analysis: level={risk_level.value}, score={risk_score:.2f}, keywords={len(triggered)}")
        
        return SafetyResult(
            risk_level=risk_level,
            risk_score=risk_score,
            triggered_keywords=triggered,
            requires_escalation=requires_escalation,
            safe_response=safe_response
        )
    
    def validate_response(self, response: str) -> Tuple[bool, Optional[str]]:
        """
        Validate an LLM response for safety.
        
        Args:
            response: The LLM-generated response
            
        Returns:
            Tuple of (is_safe, issue_description)
        """
        # Check for potentially harmful advice patterns
        harmful_patterns = [
            r"you should (end|take) your life",
            r"here's how to (harm|hurt|kill)",
            r"I recommend (self-harm|suicide)",
        ]
        
        for pattern in harmful_patterns:
            if re.search(pattern, response, re.IGNORECASE):
                return False, f"Response contains potentially harmful content: {pattern}"
        
        return True, None


# Singleton instance
_safety_service: Optional[SafetyService] = None


def get_safety_service() -> SafetyService:
    """Get the safety service singleton instance."""
    global _safety_service
    if _safety_service is None:
        _safety_service = SafetyService()
    return _safety_service
