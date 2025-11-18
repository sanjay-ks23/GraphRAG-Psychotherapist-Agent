from langgraph.graph import StateGraph, END
from ..schemas import GraphState
from .nodes import (
    retrieve_from_vectorstore,
    retrieve_from_graph,
    generate_response,
    rewrite_query,
)
from ..services.llm_service import get_chat_model
from langchain_core.messages import HumanMessage

def should_continue(state: GraphState) -> str:
    """
    Determines whether to continue with the graph or end.
    For now, it always ends after generation.
    """
    # This is a simple conditional edge.
    # It can be expanded for more complex logic, e.g., checking if the
    # response is satisfactory or if more retrieval steps are needed.
    return "end"

# Define the graph
def create_graph():
    """
    Creates the LangGraph for the RAG pipeline.
    """
    workflow = StateGraph(GraphState)

    # Define the nodes
    workflow.add_node("rewrite_query", rewrite_query)
    workflow.add_node("vectorstore_retriever", retrieve_from_vectorstore)
    workflow.add_node("graph_retriever", retrieve_from_graph)
    workflow.add_node("generate", generate_response)

    # Build the graph
    workflow.set_entry_point("rewrite_query")
    
    # The user's query is rewritten to be more specific for retrieval
    workflow.add_edge("rewrite_query", "vectorstore_retriever")
    
    # Retrieve from both vector store and graph in parallel
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
        })

    return invoke_graph

# Create a runnable instance of the graph
runnable_graph = create_graph()
