"""Response streamer: prepare final response"""
from __future__ import annotations
import time
from orchestrator.graph_dag import PipelineState
from core.utils import get_logger

logger = get_logger(__name__)

async def response_streamer_node(state: PipelineState) -> PipelineState:
    start = time.time()
    logger.info(f"Response prepared: {state.safety_level}")
    state.node_timings["response_stream"] = time.time() - start
    return state
