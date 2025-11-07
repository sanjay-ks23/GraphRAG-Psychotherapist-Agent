"""Safety postfilter: validate LLM output"""
from __future__ import annotations
import time
from orchestrator.graph_dag import PipelineState
from services.safety_service import safety_service
from core.utils import get_logger

logger = get_logger(__name__)

async def safety_postfilter_node(state: PipelineState) -> PipelineState:
    start = time.time()
    result = await safety_service.check_output(state.llm_response)
    if result["score"] > state.safety_score:
        state.safety_score = result["score"]
        state.safety_level = result["level"]
    if result["should_escalate"]:
        state.should_escalate = True
    state.node_timings["safety_postfilter"] = time.time() - start
    return state
