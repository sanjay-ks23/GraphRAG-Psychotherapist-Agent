"""Safety system tests"""
from __future__ import annotations
import pytest
from services.safety_service import safety_service

@pytest.mark.asyncio
async def test_safe_input():
    result = await safety_service.check_input("I had a good day")
    assert result["level"] == "safe"

@pytest.mark.asyncio
async def test_critical_input():
    result = await safety_service.check_input("I want to kill myself")
    assert result["level"] == "critical"
    assert result["should_escalate"] is True
