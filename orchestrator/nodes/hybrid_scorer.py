"""
Hybrid scorer node: combine vector and graph results
"""
from __future__ import annotations

import time
from orchestrator.graph_dag import PipelineState
from core.settings import WEIGHT_VECTOR, WEIGHT_GRAPH, WEIGHT_NODE_SIM
from core.utils import get_logger

logger = get_logger(__name__)


async def hybrid_scorer_node(state: PipelineState) -> PipelineState:
    """Combine and score vector + graph results"""
    start = time.time()
    
    combined = []
    
    # Add vector results
    for result in state.vector_results:
        combined.append({
            "id": result["id"],
            "text": result["text"],
            "type": "vector",
            "score": WEIGHT_VECTOR * result["score"]
        })
    
    # Add graph results
    for result in state.graph_results:
        combined.append({
            "id": result["id"],
            "text": result.get("text", ""),
            "type": "graph",
            "score": WEIGHT_GRAPH * result.get("score", 0.5)
        })
    
    # Sort by hybrid score
    state.hybrid_results = sorted(combined, key=lambda x: x["score"], reverse=True)
    
    state.node_timings["hybrid_scoring"] = time.time() - start
    logger.info(f"Scored {len(state.hybrid_results)} hybrid results")
    
    return state
