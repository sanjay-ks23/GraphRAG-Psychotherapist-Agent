"""
Vector retrieval node: semantic search in Milvus
"""
from __future__ import annotations

import time
from orchestrator.graph_dag import PipelineState
from services.vector_store import vector_store
from core.settings import VECTOR_TOP_K
from core.utils import get_logger

logger = get_logger(__name__)


async def vector_retriever_node(state: PipelineState) -> PipelineState:
    """Retrieve similar chunks from vector store"""
    start = time.time()
    
    if state.query_embedding:
        state.vector_results = await vector_store.search(
            embedding=state.query_embedding,
            top_k=VECTOR_TOP_K,
            filters={"language": state.language}
        )
    
    state.node_timings["vector_retrieval"] = time.time() - start
    logger.info(f"Retrieved {len(state.vector_results)} vector results")
    
    return state
