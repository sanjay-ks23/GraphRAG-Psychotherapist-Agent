"""
Sahyog - Psychotherapy Chatbot Main Application
FastAPI entry point for desktop deployment with GPT-5 Graph-RAG
"""
from __future__ import annotations

import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from core.config import settings
from core.utils import setup_logging, get_logger
from api.routes_sessions import router as sessions_router
from api.routes_messages import router as messages_router
from api.routes_feedback import router as feedback_router
from api.routes_escalation import router as escalation_router
from mlops.monitoring import metrics_router
from services.vector_store import vector_store
from services.graph_db import graph_db
from services.embedding_service import embedding_service

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    logger.info("Starting Sahyog application...")
    
    # Initialize services
    await vector_store.connect()
    await graph_db.connect()
    await embedding_service.initialize()
    
    logger.info("All services initialized successfully")
    yield
    
    # Cleanup
    await vector_store.disconnect()
    await graph_db.disconnect()
    logger.info("Shutdown complete")


app = FastAPI(
    title="Sahyog Psychotherapy Chatbot",
    version="1.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(sessions_router, prefix="/v1")
app.include_router(messages_router, prefix="/v1")
app.include_router(feedback_router, prefix="/v1")
app.include_router(escalation_router, prefix="/v1")
app.include_router(metrics_router)

# Static UI
app.mount("/ui", StaticFiles(directory="web_client", html=True), name="ui")


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "name": "Sahyog",
        "status": "operational",
        "version": "1.0.0"
    }


if __name__ == "__main__":
    setup_logging()
    uvicorn.run(
        "app:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info"
    )
