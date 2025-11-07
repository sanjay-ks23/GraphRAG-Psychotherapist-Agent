"""Graph DAG pipeline tests"""
from __future__ import annotations
import pytest
from orchestrator.graph_dag import PipelineState, process_message

@pytest.mark.asyncio
async def test_preprocess():
    state = PipelineState(session_id="test", user_message="Hello", language="en")
    assert state.user_message == "Hello"

@pytest.mark.asyncio
async def test_process_message():
    result = await process_message("test_session", "I feel anxious", "en", "8-12")
    assert "response" in result
    assert "safety_level" in result
