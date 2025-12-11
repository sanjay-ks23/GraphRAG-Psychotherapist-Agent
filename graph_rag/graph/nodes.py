import logging
from ..schemas import GraphState
from ..services.llm_service import get_chat_model, get_embedding_model
from ..services.weaviate_service import get_weaviate_service
from ..services.neo4j_service import Neo4jService
from ..services.safety_service import get_safety_service, RiskLevel
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers.string import StrOutputParser

logger = logging.getLogger(__name__)

# --- Node Functions ---

async def safety_prefilter(state: GraphState) -> GraphState:
    """
    Checks the user's query for safety concerns before processing.
    If critical risk is detected, returns an immediate safe response.
    """
    logger.info("Executing node: safety_prefilter")
    query = state["query"]
    
    safety_service = get_safety_service()
    result = safety_service.analyze_message(query)
    
    # If critical or high risk, provide immediate safe response
    if result.requires_escalation and result.safe_response:
        logger.warning(f"Safety escalation triggered: {result.risk_level.value}")
        return {
            "response": [result.safe_response],
            "safety_escalated": True,
            "risk_level": result.risk_level.value
        }
    
    return {"safety_escalated": False, "risk_level": result.risk_level.value}

async def rewrite_query(state: GraphState) -> GraphState:
    """
    Rewrites the user's query to be more optimal for retrieval.
    For example, it can expand acronyms, fix typos, or add context from the conversation history.
    """
    logger.info("Executing node: rewrite_query")
    query = state["query"]
    history = state["conversation_history"]

    # For now, we'll use a simple rewrite. This can be a more complex chain.
    # In a real scenario, this would involve a prompt and an LLM call.
    # Example: "Given the conversation history, rewrite the user's query to be a standalone question."
    
    # This is a placeholder for the rewrite logic
    rewritten_query = query 
    
    return {"query": rewritten_query}


async def retrieve_from_vectorstore(state: GraphState) -> GraphState:
    """
    Retrieves relevant documents from the Weaviate vector store.
    """
    logger.info("Executing node: retrieve_from_vectorstore")
    query = state["query"]
    
    embedding_model = get_embedding_model()
    weaviate = get_weaviate_service()
    
    # Embed the query
    query_embedding = embedding_model.embed_query(query)
    
    # Search in Weaviate
    results = weaviate.search(query_vector=query_embedding, top_k=5)
    
    # Process results
    retrieved_docs = [result.get('chunk_id', '') for result in results]
    
    context = state.get("context", "")
    context += "\n\n--- Vector Store Documents ---\n" + "\n".join(retrieved_docs)
    
    return {"context": context, "sources": retrieved_docs}


async def retrieve_from_graph(state: GraphState) -> GraphState:
    """
    Retrieves relevant information from the Neo4j knowledge graph.
    This could involve entity extraction from the query and then finding related nodes.
    """
    logger.info("Executing node: retrieve_from_graph")
    query = state["query"]
    
    # This is a placeholder for a more sophisticated graph retrieval process.
    # A full implementation would:
    # 1. Use an LLM to extract entities (e.g., names, places) from the query.
    # 2. Query Neo4j for those entities and their neighbors.
    # 3. Serialize the resulting subgraph into a text format for the context.
    
    # Example Cypher query (if we had extracted entities)
    # query = "MATCH (e:Entity)-[r]-(n) WHERE e.name IN $entities RETURN e, r, n"
    # records = await Neo4jService.execute_query(query, {"entities": ["some_entity"]})
    
    # For now, we'll just add a placeholder message.
    graph_context = "Placeholder for data retrieved from Neo4j."
    
    context = state.get("context", "")
    context += "\n\n--- Knowledge Graph Data ---\n" + graph_context
    
    return {"context": context}


async def generate_response(state: GraphState) -> GraphState:
    """
    Generates a response using the LLM based on the retrieved context.
    """
    logger.info("Executing node: generate_response")
    query = state["query"]
    context = state["context"]
    history = state["conversation_history"]
    
    llm = get_chat_model()
    
    prompt_template = ChatPromptTemplate.from_messages([
        ("system", "You are a helpful assistant. Use the following context to answer the user's question. If you don't know the answer, just say that you don't know.\n\nContext:\n{context}"),
        ("human", "{query}")
    ])
    
    chain = prompt_template | llm | StrOutputParser()
    
    # Stream the response
    response_chunks = []
    async for chunk in chain.astream({"query": query, "context": context}):
        response_chunks.append(chunk)
        # This part is tricky with state updates. LangGraph's `astream`
        # is designed to stream final outputs, not intermediate ones.
        # For live streaming to the client, we'll handle that in the API layer.
    
    final_response = "".join(response_chunks)
    
    return {"response": [final_response]} # Using operator.add in schema
