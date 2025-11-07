"""Provenance builder: extract source attribution"""
from __future__ import annotations
import time
from orchestrator.graph_dag import PipelineState
from core.utils import format_provenance, get_logger

logger = get_logger(__name__)

async def provenance_builder_node(state: PipelineState) -> PipelineState:
    start = time.time()
    state.provenance = format_provenance(state.hybrid_results[:10])
    state.node_timings["provenance"] = time.time() - start
    return state
