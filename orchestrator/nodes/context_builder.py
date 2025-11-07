"""
Context builder node: assemble LLM context from retrieved results
"""
from __future__ import annotations

import time
from orchestrator.graph_dag import PipelineState
from core.settings import MAX_CONTEXT_SNIPPETS, MAX_CONTEXT_FACTS
from core.utils import get_logger

logger = get_logger(__name__)


async def context_builder_node(state: PipelineState) -> PipelineState:
    """Build context from hybrid results"""
    start = time.time()
    
    # Take top results
    top_results = state.hybrid_results[:MAX_CONTEXT_SNIPPETS + MAX_CONTEXT_FACTS]
    
    # Build context string
    context_parts = []
    context_parts.append("Relevant therapeutic knowledge:\n")
    
    for i, result in enumerate(top_results, 1):
        if result["text"]:
            context_parts.append(f"{i}. {result['text'][:300]}")
    
    state.context = "\n".join(context_parts)
    
    # Build prompt
    state.prompt = f"""You are Sahyog, an empathetic AI counselor for children and adolescents.

Context:
{state.context}

User ({state.age_range} years old): {state.user_message}

Provide a supportive, age-appropriate response that helps the child understand and manage their feelings. Use the context provided to give evidence-based guidance."""
    
    state.node_timings["context_building"] = time.time() - start
    logger.info(f"Built context with {len(top_results)} sources")
    
    return state
