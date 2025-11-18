import logging
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from graph_rag.schemas import ChatRequest
from graph_rag.graph.graph import runnable_graph
from graph_rag.services.neo4j_service import Neo4jService
from graph_rag.settings import settings

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Rate Limiting Setup ---
limiter = Limiter(key_func=get_remote_address, default_limits=[settings.RATE_LIMIT])

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handle startup and shutdown events for the application.
    """
    logger.info("Application startup: Initializing services...")
    # Initialize Neo4j driver
    await Neo4jService.get_driver()
    yield
    logger.info("Application shutdown: Closing services...")
    # Close Neo4j driver
    await Neo4jService.close_driver()

app = FastAPI(
    title="Graph RAG API",
    description="A production-grade RAG application using LangGraph, Neo4j, and Milvus.",
    version="1.0.0",
    lifespan=lifespan
)

# --- Rate Limiting Middleware ---
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# --- CORS Configuration ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this to your frontend's domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- API Endpoints ---

@app.get("/", summary="Health check endpoint")
def read_root():
    """
    Health check endpoint to ensure the server is running.
    """
    return {"status": "ok"}

@app.post("/chat", summary="Handle a chat request and stream the response")
@limiter.limit(settings.RATE_LIMIT)
async def chat_endpoint(request: ChatRequest, req: Request):
    """
    Endpoint to handle a chat message.
    It invokes the RAG graph and streams the response back to the client.
    """
    query = request.get("query")
    if not query:
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    logger.info(f"Received chat request with query: {query}")

    async def stream_response():
        """
        Generator function to stream the graph's output.
        """
        try:
            # The `runnable_graph` is already configured to be a streaming function
            async for chunk in runnable_graph.astream({"query": query, "conversation_history": [], "response": []}):
                # Each `chunk` is a dictionary representing the state of the graph
                # at that point. We are interested in the 'response' key.
                if "response" in chunk:
                    response_part = chunk["response"][-1] # Get the latest piece of the response
                    yield response_part
        except Exception as e:
            logger.error(f"Error during graph execution: {e}")
            # In a real app, you might want to stream an error message
            yield "An error occurred while processing your request."

    return StreamingResponse(stream_response(), media_type="text/plain")

# --- Main execution ---
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.API_HOST, port=settings.API_PORT)
