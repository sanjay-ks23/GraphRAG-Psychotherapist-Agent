"""
Preprocessing node: normalize text and generate embedding
"""
from __future__ import annotations

import time
from orchestrator.graph_dag import PipelineState
from services.embedding_service import embedding_service
from core.utils import sanitize_input, get_logger

logger = get_logger(__name__)


async def preprocess_node(state: PipelineState) -> PipelineState:
    """Preprocess user message and generate query embedding"""
    start = time.time()
    
    # Sanitize input
    state.user_message = sanitize_input(state.user_message)
    
    # Generate embedding
    state.query_embedding = await embedding_service.embed_text(state.user_message)
    
    state.node_timings["preprocess"] = time.time() - start
    logger.info(f"Preprocessed message: {len(state.query_embedding)} dims")
    
    return state
