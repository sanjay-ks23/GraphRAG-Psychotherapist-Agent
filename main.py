"""
GraphRAG Mental Wellness API - Production-Grade FastAPI Backend

Provides REST API endpoints for the hybrid GraphRAG pipeline with
real-time safety guardrails and comprehensive observability.
"""
import logging
import uuid
from pythonjsonlogger import jsonlogger
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from starlette.middleware.base import BaseHTTPMiddleware

from graph_rag.schemas import ChatRequest
from graph_rag.services.redis_service import cache_llm_response
from graph_rag.graph.graph import runnable_graph
from graph_rag.services.neo4j_service import Neo4jService
from graph_rag.services.weaviate_service import get_weaviate_service
from graph_rag.settings import settings

# --- JSON Logging Configuration ---
for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)

logHandler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter(
    '%(asctime)s %(name)s %(levelname)s %(message)s %(request_id)s',
    defaults={'request_id': 'N/A'}
)
logHandler.setFormatter(formatter)
logging.root.addHandler(logHandler)
logging.root.setLevel(logging.INFO)

logger = logging.getLogger(__name__)


# --- Request ID Middleware ---
class RequestIDMiddleware(BaseHTTPMiddleware):
    """Add unique request ID to each request for tracing."""
    
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())[:8]
        request.state.request_id = request_id
        
        # Add to logging context
        logger_adapter = logging.LoggerAdapter(
            logger, {'request_id': request_id}
        )
        
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


# --- Rate Limiting Setup ---
limiter = Limiter(key_func=get_remote_address, default_limits=[settings.RATE_LIMIT])


# --- Application State ---
class AppState:
    """Track application health state."""
    is_ready: bool = False
    neo4j_connected: bool = False
    weaviate_connected: bool = False


app_state = AppState()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handle startup and shutdown events for the application.
    Initializes and cleans up database connections gracefully.
    """
    logger.info("Application startup: Initializing services...")
    
    try:
        # Initialize Neo4j
        await Neo4jService.get_driver()
        app_state.neo4j_connected = True
        logger.info("Neo4j connected successfully")
    except Exception as e:
        logger.error(f"Failed to connect to Neo4j: {e}")
        app_state.neo4j_connected = False
    
    try:
        # Initialize Weaviate (lazy loading, just verify it can connect)
        get_weaviate_service()
        app_state.weaviate_connected = True
        logger.info("Weaviate connected successfully")
    except Exception as e:
        logger.error(f"Failed to connect to Weaviate: {e}")
        app_state.weaviate_connected = False
    
    app_state.is_ready = app_state.neo4j_connected and app_state.weaviate_connected
    logger.info(f"Application ready: {app_state.is_ready}")
    
    yield
    
    logger.info("Application shutdown: Closing services...")
    
    # Close Neo4j
    try:
        await Neo4jService.close_driver()
        logger.info("Neo4j connection closed")
    except Exception as e:
        logger.error(f"Error closing Neo4j: {e}")
    
    # Close Weaviate
    try:
        weaviate = get_weaviate_service()
        weaviate.close()
        logger.info("Weaviate connection closed")
    except Exception as e:
        logger.error(f"Error closing Weaviate: {e}")


app = FastAPI(
    title="GraphRAG Mental Wellness API",
    description="A production-grade Hybrid GraphRAG application using LangGraph, Neo4j, and Weaviate for mental wellness support.",
    version="1.0.0",
    lifespan=lifespan
)

# --- Middleware ---
app.add_middleware(RequestIDMiddleware)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to your frontend domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Health Check Endpoints ---

@app.get("/", summary="Basic health check")
def read_root():
    """Basic health check to verify the server is running."""
    return {"status": "ok", "service": "graphrag-mental-wellness"}


@app.get("/health", summary="Liveness probe")
def health_check():
    """
    Liveness probe for Kubernetes/container orchestration.
    Returns 200 if the application process is alive.
    """
    return {"status": "alive"}


@app.get("/ready", summary="Readiness probe")
def readiness_check():
    """
    Readiness probe for Kubernetes/container orchestration.
    Returns 200 only if all dependent services are connected.
    """
    if not app_state.is_ready:
        return JSONResponse(
            status_code=503,
            content={
                "status": "not_ready",
                "neo4j": app_state.neo4j_connected,
                "weaviate": app_state.weaviate_connected,
            }
        )
    
    return {
        "status": "ready",
        "neo4j": app_state.neo4j_connected,
        "weaviate": app_state.weaviate_connected,
    }


# --- Chat Endpoint ---

@app.post("/chat", summary="Handle a chat request and stream the response")
@limiter.limit(settings.RATE_LIMIT)
async def chat_endpoint(request: ChatRequest, req: Request):
    """
    Main chat endpoint for the mental wellness agent.
    
    - Processes the query through the GraphRAG pipeline with safety guardrails
    - Streams the response back to the client
    - Includes automatic safety escalation for crisis situations
    """
    query = request.get("query")
    if not query:
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    
    if len(query) > 5000:
        raise HTTPException(status_code=400, detail="Query too long (max 5000 characters)")
    
    request_id = getattr(req.state, 'request_id', 'unknown')
    logger.info(f"Chat request received", extra={'request_id': request_id, 'query_length': len(query)})

    async def stream_response():
        """Generator function to stream the graph's output."""
        try:
            async for chunk in runnable_graph.astream({
                "query": query,
                "conversation_history": [],
                "response": [],
                "safety_escalated": False,
                "risk_level": None,
            }):
                if "response" in chunk and chunk["response"]:
                    response_part = chunk["response"][-1]
                    yield response_part
        except Exception as e:
            logger.error(f"Error during graph execution: {e}", extra={'request_id': request_id})
            yield "I apologize, but I encountered an error processing your request. If you're in crisis, please contact emergency services or call 988."

    return StreamingResponse(stream_response(), media_type="text/plain")


# --- Main execution ---
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.API_HOST, port=settings.API_PORT)

