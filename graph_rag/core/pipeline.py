"""
Core Pipeline - LangGraph RAG workflow.

Consolidates graph/nodes.py and graph/graph.py into single module.
"""
import logging
from typing import List
from langgraph.graph import StateGraph, END
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from graph_rag.services import get_chat_model, get_embedding_model, cache, vectorstore, graphdb

logger = logging.getLogger(__name__)


# === State Definition ===

class PipelineState(dict):
    """Pipeline state passed between nodes."""
    pass


# === Node Functions ===

async def safety_check(state: PipelineState) -> PipelineState:
    """Check query for safety concerns."""
    query = state.get("query", "").lower()
    
    # Critical risk keywords
    critical = ["suicide", "kill myself", "end my life", "want to die"]
    if any(kw in query for kw in critical):
        logger.warning("Safety: Critical risk detected")
        return {
            **state,
            "safety_triggered": True,
            "response": [
                "I'm concerned about what you've shared. Your safety matters. "
                "Please contact the 988 Suicide & Crisis Lifeline (call/text 988) immediately. "
                "You're not alone, and help is available 24/7."
            ]
        }
    
    return {**state, "safety_triggered": False}


async def retrieve_context(state: PipelineState) -> PipelineState:
    """Retrieve context from vector store and knowledge graph."""
    if state.get("safety_triggered"):
        return state
    
    query = state.get("query", "")
    context_parts = []
    sources = []
    
    try:
        # Vector search
        embedding_model = get_embedding_model()
        
        # Check embedding cache
        embedding = cache.get_cached_embedding(query)
        if not embedding:
            embedding = embedding_model.embed_query(query)
            cache.cache_embedding(query, embedding)
        
        results = vectorstore.search(embedding, top_k=5)
        for r in results:
            if r.get("content"):
                context_parts.append(r["content"])
                sources.append(r.get("chunk_id", ""))
        
        # Graph search - extract topics
        topics = extract_topics(query)
        for topic in topics[:3]:
            entities = await graphdb.get_related_entities(topic)
            for e in entities[:5]:
                rel_str = f"{e.get('source')} → {e.get('target')}"
                context_parts.append(rel_str)
        
    except Exception as e:
        logger.error(f"Retrieval error: {e}")
    
    context = "\n\n".join(context_parts) if context_parts else ""
    return {**state, "context": context, "sources": sources}


def extract_topics(query: str) -> List[str]:
    """Extract mental wellness topics from query."""
    topics = [
        "anxiety", "depression", "stress", "sleep", "mindfulness",
        "meditation", "breathing", "panic", "therapy", "cbt",
        "relaxation", "wellness", "coping", "grief", "anger"
    ]
    found = [t for t in topics if t in query.lower()]
    return found if found else ["wellness"]


async def generate_response(state: PipelineState) -> PipelineState:
    """Generate LLM response with retrieved context."""
    if state.get("safety_triggered"):
        return state
    
    query = state.get("query", "")
    context = state.get("context", "")
    history = state.get("history", [])
    
    # Check cache
    cached = cache.get_cached_response(query)
    if cached:
        logger.info("Response cache hit")
        return {**state, "response": [cached]}
    
    llm = get_chat_model()
    
    system = """You are a compassionate mental wellness assistant.
    
Guidelines:
- Be empathetic and supportive
- Provide evidence-based guidance
- Suggest professional help for serious concerns
- Never diagnose or prescribe

Context:
{context}

Note: You provide general wellness information, not medical advice."""

    prompt = ChatPromptTemplate.from_messages([
        ("system", system),
        ("human", "{query}")
    ])
    
    chain = prompt | llm | StrOutputParser()
    
    try:
        response = ""
        async for chunk in chain.astream({"query": query, "context": context}):
            response += chunk
        
        # Cache response
        if response:
            cache.cache_response(query, response)
        
        return {**state, "response": [response]}
    
    except Exception as e:
        logger.error(f"Generation error: {e}")
        return {
            **state,
            "response": [
                "I apologize, but I'm having trouble responding. "
                "If you need support, please call 988 for the Crisis Lifeline."
            ]
        }


def should_end_early(state: PipelineState) -> str:
    """Route based on safety check."""
    return "end" if state.get("safety_triggered") else "continue"


# === Build Graph ===

def build_pipeline() -> StateGraph:
    """Construct the LangGraph pipeline."""
    workflow = StateGraph(PipelineState)
    
    # Add nodes
    workflow.add_node("safety", safety_check)
    workflow.add_node("retrieve", retrieve_context)
    workflow.add_node("generate", generate_response)
    
    # Add edges
    workflow.set_entry_point("safety")
    workflow.add_conditional_edges(
        "safety",
        should_end_early,
        {"end": END, "continue": "retrieve"}
    )
    workflow.add_edge("retrieve", "generate")
    workflow.add_edge("generate", END)
    
    return workflow.compile()


# Compiled pipeline instance
pipeline = build_pipeline()
