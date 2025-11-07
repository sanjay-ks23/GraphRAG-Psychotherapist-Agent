"""Feedback collection routes"""
from __future__ import annotations
from fastapi import APIRouter
from pydantic import BaseModel
from core.utils import get_logger

logger = get_logger(__name__)
router = APIRouter(tags=["feedback"])

class FeedbackRequest(BaseModel):
    session_id: str
    message_id: str
    rating: int
    comment: str = ""

@router.post("/feedback")
async def submit_feedback(request: FeedbackRequest):
    logger.info(f"Feedback received: {request.session_id} - Rating: {request.rating}")
    return {"success": True, "message": "Feedback recorded"}
