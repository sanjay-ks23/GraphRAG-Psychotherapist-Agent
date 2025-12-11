from typing import List, TypedDict, Annotated, Dict, Optional
from langchain_core.messages import BaseMessage
import operator

# --- API Schemas ---

class ChatRequest(TypedDict):
    """Request schema for the chat endpoint."""
    query: str
    session_id: str | None = None

# --- Graph State Schema ---

class GraphState(TypedDict):
    """
    Represents the state of our graph.

    Attributes:
        query: The user's question.
        context: The retrieved context from knowledge graph and vector store.
        conversation_history: The history of the conversation.
        response: The LLM response.
        sources: A list of source documents used for the response.
        safety_escalated: Whether a safety escalation was triggered.
        risk_level: The assessed risk level of the query.
    """
    query: str
    context: str
    conversation_history: List[BaseMessage]
    response: Annotated[list[str], operator.add]
    sources: List[str]
    safety_escalated: Optional[bool]
    risk_level: Optional[str]

