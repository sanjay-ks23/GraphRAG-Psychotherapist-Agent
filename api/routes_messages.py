"""Message handling routes"""
from __future__ import annotations
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from orchestrator.graph_dag import process_message
from orchestrator.nodes.llm_invoker_gpt5 import llm_invoke_streaming
from core.utils import get_logger

logger = get_logger(__name__)
router = APIRouter(tags=["messages"])

class MessageRequest(BaseModel):
    session_id: str
    content: str
    language: str = "en"

class MessageResponse(BaseModel):
    response: str
    safety_level: str
    provenance: list
    escalated: bool

@router.post("/messages", response_model=MessageResponse)
async def send_message(request: MessageRequest):
    result = await process_message(
        session_id=request.session_id,
        user_message=request.content,
        language=request.language
    )
    return MessageResponse(**result)

@router.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_json()
            message = data.get("message", "")
            async def send_token(token: str):
                await websocket.send_json({"token": token})
            await llm_invoke_streaming(message, send_token)
    except WebSocketDisconnect:
        logger.info(f"WebSocket closed: {session_id}")
