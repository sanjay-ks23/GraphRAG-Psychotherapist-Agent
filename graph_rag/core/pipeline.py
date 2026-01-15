"""LangGraph Pipeline"""
import logging
from typing import List
from langgraph.graph import StateGraph, END
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from graph_rag.services import get_chat_model, get_embedding_model, cache, vectorstore, graphdb

logger = logging.getLogger(__name__)


class PipelineState(dict):
    pass


async def safety_check(state: PipelineState) -> PipelineState:
    query = state.get("query", "").lower()
    critical = ["suicide", "kill myself", "end my life", "want to die"]
    if any(kw in query for kw in critical):
        return {**state, "safety_triggered": True, "response": [
            "I'm deeply concerned about what you've shared. Your life has value.\n\nPlease reach out for help immediately:\n- **Vandrevala Foundation**: 1860-266-2345 (24x7)\n- **KIRAN Helpline**: 1800-599-0019\n- **iCall**: 91529-87821\n\nYou are not alone."
        ]}
    return {**state, "safety_triggered": False}


async def retrieve_context(state: PipelineState) -> PipelineState:
    if state.get("safety_triggered"):
        return state
    
    query = state.get("query", "")
    context_parts, sources = [], []
    
    try:
        embedding = cache.get_cached_embedding(query)
        if not embedding:
            embedding = get_embedding_model().embed_query(query)
            cache.cache_embedding(query, embedding)
        
        for r in vectorstore.search(embedding, top_k=5):
            if r.get("content"):
                context_parts.append(r["content"])
                sources.append(r.get("chunk_id", ""))
        
        topics = [t for t in ["anxiety", "depression", "stress", "sleep", "mindfulness", "yoga", "family", "exam", "career", "parents"] if t in query.lower()]
        for topic in (topics or ["wellness"])[:3]:
            for e in (await graphdb.get_related_entities(topic))[:5]:
                context_parts.append(f"{e.get('source')} → {e.get('target')}")
    except Exception as e:
        logger.error(f"Retrieval: {e}")
    
    return {**state, "context": "\n\n".join(context_parts), "sources": sources}


async def generate_response(state: PipelineState) -> PipelineState:
    if state.get("safety_triggered"):
        return state
    
    query, context = state.get("query", ""), state.get("context", "")
    
    cached = cache.get_cached_response(query)
    if cached:
        return {**state, "response": [cached]}
    
    system_prompt = """You are a compassionate mental wellness companion.
    
Guidelines:
- Be empathetic, professional, and respectful.
- Provide evidence-based guidance and holistic suggestions (e.g., mindfulness, breathing exercises).
- Suggest professional help for serious concerns.
- Never diagnose.

Context:
{context}"""

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "{query}")
    ])
    
    chain = prompt | get_chat_model() | StrOutputParser()
    
    try:
        response = ""
        async for chunk in chain.astream({"query": query, "context": context}):
            response += chunk
        if response:
            cache.cache_response(query, response)
        return {**state, "response": [response]}
    except Exception as e:
        logger.error(f"Generation: {e}")
        return {**state, "response": ["I apologize, I'm having trouble connecting. If you are in distress, please call the KIRAN Helpline at 1800-599-0019."]}


def should_end_early(state: PipelineState) -> str:
    return "end" if state.get("safety_triggered") else "continue"


def build_pipeline() -> StateGraph:
    workflow = StateGraph(PipelineState)
    workflow.add_node("safety", safety_check)
    workflow.add_node("retrieve", retrieve_context)
    workflow.add_node("generate", generate_response)
    workflow.set_entry_point("safety")
    workflow.add_conditional_edges("safety", should_end_early, {"end": END, "continue": "retrieve"})
    workflow.add_edge("retrieve", "generate")
    workflow.add_edge("generate", END)
    return workflow.compile()


pipeline = build_pipeline()
