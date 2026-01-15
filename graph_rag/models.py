"""
Pydantic Models - API schemas and state definitions.

Consolidated from schemas/ directory.
"""
from typing import Optional, List, Annotated
from pydantic import BaseModel, Field
import operator


# === API Request/Response Models ===

class ChatRequest(BaseModel):
    """Chat endpoint request."""
    query: str = Field(..., min_length=1, max_length=5000)
    session_id: Optional[str] = None


class ChatStreamRequest(BaseModel):
    """Streaming chat request."""
    query: str = Field(..., min_length=1, max_length=5000)
    session_id: Optional[str] = None
    history: Optional[List[dict]] = None


class ChatResponse(BaseModel):
    """Chat endpoint response."""
    response: str
    session_id: str
    sources: List[str] = []


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    neo4j: bool = False
    weaviate: bool = False
    redis: bool = False


class DocumentUpload(BaseModel):
    """Document upload response."""
    doc_id: str
    filename: str
    chunks: int
    chars: int


# === LangGraph State ===

class GraphState(dict):
    """
    LangGraph pipeline state.
    
    Using dict base for LangGraph compatibility.
    """
    query: str = ""
    context: str = ""
    history: List[dict] = []
    response: Annotated[List[str], operator.add] = []
    sources: List[str] = []
    safety_triggered: bool = False
    risk_level: Optional[str] = None
