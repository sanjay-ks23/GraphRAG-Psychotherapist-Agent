"""
Safety prefilter node: fast risk triage
"""
from __future__ import annotations

import time
from orchestrator.graph_dag import PipelineState
from services.safety_service import safety_service
from core.utils import get_logger

logger = get_logger(__name__)


async def safety_prefilter_node(state: PipelineState) -> PipelineState:
    """Fast safety check before retrieval"""
    start = time.time()
    
    result = await safety_service.check_input(state.user_message)
    
    state.safety_level = result["level"]
    state.safety_score = result["score"]
    state.should_escalate = result["should_escalate"]
    state.skip_llm = result["should_escalate"]
    
    state.node_timings["safety_prefilter"] = time.time() - start
    
    if state.should_escalate:
        logger.warning(f"Message flagged: {state.safety_level} (score: {state.safety_score})")
    
    return state
