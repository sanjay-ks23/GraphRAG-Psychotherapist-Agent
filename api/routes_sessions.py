"""Session management routes"""
from __future__ import annotations
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime, timedelta
import jwt
from core.config import settings
from core.utils import generate_id, get_logger

logger = get_logger(__name__)
router = APIRouter(tags=["sessions"])

class CreateSessionRequest(BaseModel):
    user_id: str
    consent_token: str
    language: str = "en"
    age_range: str = "8-12"

class SessionResponse(BaseModel):
    session_id: str
    jwt_token: str
    expires_at: datetime

@router.post("/sessions", response_model=SessionResponse)
async def create_session(request: CreateSessionRequest):
    session_id = generate_id("sess")
    expires_at = datetime.utcnow() + timedelta(hours=1)
    token = jwt.encode(
        {"session_id": session_id, "exp": expires_at},
        settings.JWT_SECRET,
        algorithm="HS256"
    )
    logger.info(f"Created session: {session_id}")
    return SessionResponse(
        session_id=session_id,
        jwt_token=token,
        expires_at=expires_at
    )
