from langgraph.graph import StateGraph, END
from ..schemas import GraphState
from .nodes import (
    retrieve_from_vectorstore,
    retrieve_from_graph,
    generate_response,
    rewrite_query,
    safety_prefilter,
)
from ..services.llm_service import get_chat_model
from langchain_core.messages import HumanMessage


def should_continue(state: GraphState) -> str:
    """
    Determines whether to continue with the graph or end.
    For now, it always ends after generation.
    """
    return "end"


def check_safety_escalation(state: GraphState) -> str:
    """
    Check if safety escalation was triggered.
    If so, skip to end. Otherwise, continue with normal pipeline.
    """
    if state.get("safety_escalated", False):
        return "end"
    return "continue"


# Define the graph
def create_graph():
    """
    Creates the LangGraph for the RAG pipeline with safety guardrails.
    """
    workflow = StateGraph(GraphState)

    # Define the nodes
    workflow.add_node("safety_prefilter", safety_prefilter)
    workflow.add_node("rewrite_query", rewrite_query)
    workflow.add_node("vectorstore_retriever", retrieve_from_vectorstore)
    workflow.add_node("graph_retriever", retrieve_from_graph)
    workflow.add_node("generate", generate_response)

    # Build the graph - start with safety check
    workflow.set_entry_point("safety_prefilter")
    
    # After safety check, either end (if escalated) or continue
    workflow.add_conditional_edges(
        "safety_prefilter",
        check_safety_escalation,
        {
            "end": END,
            "continue": "rewrite_query",
        },
    )
    
    # The user's query is rewritten to be more specific for retrieval
    workflow.add_edge("rewrite_query", "vectorstore_retriever")
    
    # Retrieve from both vector store and graph
    workflow.add_edge("vectorstore_retriever", "graph_retriever")
    workflow.add_edge("graph_retriever", "generate")
    
    # After generation, we decide whether to end or continue
    workflow.add_conditional_edges(
        "generate",
        should_continue,
        {
            "end": END,
        },
    )

    # Compile the graph into a runnable
    graph = workflow.compile()
    
    # Add a convenience method to invoke the graph with a query
    def invoke_graph(query: str, history: list = []):
        return graph.stream({
            "query": query,
            "conversation_history": [HumanMessage(content=h) for h in history],
            "response": [],
            "safety_escalated": False,
            "risk_level": None,
        })

    return invoke_graph


# Create a runnable instance of the graph
runnable_graph = create_graph()

