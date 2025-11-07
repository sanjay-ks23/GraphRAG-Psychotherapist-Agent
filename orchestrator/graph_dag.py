"""
Main LangGraph DAG definition for Graph-RAG pipeline
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from langgraph.graph import StateGraph, END

from orchestrator.nodes.preprocess import preprocess_node
from orchestrator.nodes.safety_prefilter import safety_prefilter_node
from orchestrator.nodes.vector_retriever import vector_retriever_node
from orchestrator.nodes.kg_mapper import kg_mapper_node
from orchestrator.nodes.hybrid_scorer import hybrid_scorer_node
from orchestrator.nodes.context_builder import context_builder_node
from orchestrator.nodes.llm_invoker_gpt5 import llm_invoker_node
from orchestrator.nodes.safety_postfilter import safety_postfilter_node
from orchestrator.nodes.provenance_builder import provenance_builder_node
from orchestrator.nodes.response_streamer import response_streamer_node
from core.utils import get_logger

logger = get_logger(__name__)


@dataclass
class PipelineState:
    """State object passed through pipeline nodes"""
    session_id: str
    user_message: str
    language: str = "en"
    age_range: str = "8-12"
    
    # Processing artifacts
    query_embedding: list[float] | None = None
    vector_results: list[dict] = field(default_factory=list)
    graph_results: list[dict] = field(default_factory=list)
    hybrid_results: list[dict] = field(default_factory=list)
    context: str = ""
    prompt: str = ""
    llm_response: str = ""
    safety_level: str = "safe"
    safety_score: float = 0.0
    should_escalate: bool = False
    skip_llm: bool = False
    provenance: list[dict] = field(default_factory=list)
    
    # Metadata
    node_timings: dict[str, float] = field(default_factory=dict)
    error: str | None = None


def build_graph() -> StateGraph:
    """Build and compile the LangGraph DAG"""
    
    workflow = StateGraph(PipelineState)
    
    # Add nodes
    workflow.add_node("preprocess", preprocess_node)
    workflow.add_node("safety_prefilter", safety_prefilter_node)
    workflow.add_node("vector_retriever", vector_retriever_node)
    workflow.add_node("kg_mapper", kg_mapper_node)
    workflow.add_node("hybrid_scorer", hybrid_scorer_node)
    workflow.add_node("context_builder", context_builder_node)
    workflow.add_node("llm_invoker", llm_invoker_node)
    workflow.add_node("safety_postfilter", safety_postfilter_node)
    workflow.add_node("provenance_builder", provenance_builder_node)
    workflow.add_node("response_streamer", response_streamer_node)
    
    # Define edges
    workflow.set_entry_point("preprocess")
    workflow.add_edge("preprocess", "safety_prefilter")
    
    # Conditional after safety prefilter
    workflow.add_conditional_edges(
        "safety_prefilter",
        lambda state: "escalate" if state.should_escalate else "continue",
        {
            "continue": "vector_retriever",
            "escalate": END
        }
    )
    
    # Parallel retrieval would be here (simplified as sequential)
    workflow.add_edge("vector_retriever", "kg_mapper")
    workflow.add_edge("kg_mapper", "hybrid_scorer")
    workflow.add_edge("hybrid_scorer", "context_builder")
    
    # Conditional to skip LLM if flagged
    workflow.add_conditional_edges(
        "context_builder",
        lambda state: "skip" if state.skip_llm else "llm",
        {
            "llm": "llm_invoker",
            "skip": END
        }
    )
    
    workflow.add_edge("llm_invoker", "safety_postfilter")
    workflow.add_edge("safety_postfilter", "provenance_builder")
    workflow.add_edge("provenance_builder", "response_streamer")
    workflow.add_edge("response_streamer", END)
    
    return workflow.compile()


# Global compiled graph
graph = build_graph()


async def process_message(
    session_id: str,
    user_message: str,
    language: str = "en",
    age_range: str = "8-12"
) -> dict[str, Any]:
    """
    Process a user message through the Graph-RAG pipeline
    
    Args:
        session_id: Unique session identifier
        user_message: User's input message
        language: Language code
        age_range: User's age range
        
    Returns:
        Response dict with message and metadata
    """
    logger.info(f"Processing message for session {session_id}")
    
    initial_state = PipelineState(
        session_id=session_id,
        user_message=user_message,
        language=language,
        age_range=age_range
    )
    
    try:
        final_state = await graph.ainvoke(initial_state)
        
        return {
            "response": final_state.llm_response,
            "safety_level": final_state.safety_level,
            "safety_score": final_state.safety_score,
            "provenance": final_state.provenance,
            "escalated": final_state.should_escalate,
            "timings": final_state.node_timings
        }
        
    except Exception as e:
        logger.error(f"Pipeline error: {str(e)}")
        return {
            "response": "I apologize, but I'm having trouble right now. Please try again.",
            "safety_level": "error",
            "safety_score": 0.0,
            "provenance": [],
            "escalated": False,
            "error": str(e)
        }
