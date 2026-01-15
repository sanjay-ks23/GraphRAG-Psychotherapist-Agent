"""Pydantic Models"""
from typing import Optional, List, Annotated
from pydantic import BaseModel, Field
import operator


class ChatRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=5000)
    session_id: Optional[str] = None


class ChatStreamRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=5000)
    session_id: Optional[str] = None
    history: Optional[List[dict]] = None


class ChatResponse(BaseModel):
    response: str
    session_id: str
    sources: List[str] = []


class HealthResponse(BaseModel):
    status: str
    neo4j: bool = False
    weaviate: bool = False
    redis: bool = False


class GraphState(dict):
    query: str = ""
    context: str = ""
    history: List[dict] = []
    response: Annotated[List[str], operator.add] = []
    sources: List[str] = []
    safety_triggered: bool = False
    risk_level: Optional[str] = None
