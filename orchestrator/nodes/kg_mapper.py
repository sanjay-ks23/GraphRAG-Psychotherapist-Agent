"""
Knowledge graph mapper node: find seed nodes and expand
"""
from __future__ import annotations

import time
from orchestrator.graph_dag import PipelineState
from services.graph_db import graph_db
from core.settings import GRAPH_MAX_HOPS, GRAPH_MAX_NODES
from core.utils import get_logger

logger = get_logger(__name__)


async def kg_mapper_node(state: PipelineState) -> PipelineState:
    """Map query to knowledge graph and expand"""
    start = time.time()
    
    # Find seed nodes
    seed_nodes = await graph_db.find_seed_nodes(
        text=state.user_message,
        language=state.language
    )
    
    # Expand graph
    if seed_nodes:
        state.graph_results = await graph_db.expand_graph(
            seed_ids=[n["id"] for n in seed_nodes],
            max_hops=GRAPH_MAX_HOPS,
            max_nodes=GRAPH_MAX_NODES
        )
    
    state.node_timings["kg_mapping"] = time.time() - start
    logger.info(f"Retrieved {len(state.graph_results)} graph results")
    
    return state
