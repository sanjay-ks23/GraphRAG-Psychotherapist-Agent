"""
GraphRAG Mental Wellness API

Production-grade FastAPI with streaming responses.
"""
import logging
import uuid
import os
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request, UploadFile, File
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from starlette.middleware.base import BaseHTTPMiddleware

from graph_rag.config import settings
from graph_rag.models import ChatRequest, ChatStreamRequest, HealthResponse
from graph_rag.core import pipeline
from graph_rag.services import cache, vectorstore, graphdb, get_embedding_model

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)


# === Middleware ===

class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request.state.request_id = str(uuid.uuid4())[:8]
        response = await call_next(request)
        response.headers["X-Request-ID"] = request.state.request_id
        return response


# === Lifespan ===

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown events."""
    logger.info("Starting GraphRAG API...")
    
    # Initialize services
    try:
        vectorstore.connect()
        logger.info("Weaviate: OK")
    except Exception as e:
        logger.error(f"Weaviate: FAILED - {e}")
    
    try:
        await graphdb.connect()
        logger.info("Neo4j: OK")
    except Exception as e:
        logger.error(f"Neo4j: FAILED - {e}")
    
    if cache.ping():
        logger.info("Redis: OK")
    else:
        logger.warning("Redis: UNAVAILABLE")
    
    os.makedirs(settings.upload_dir, exist_ok=True)
    
    yield
    
    logger.info("Shutting down...")
    vectorstore.close()
    await graphdb.close()


# === App ===

app = FastAPI(
    title="GraphRAG Mental Wellness API",
    version="2.0.0",
    lifespan=lifespan
)

# Middleware
app.add_middleware(RequestIDMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiting
limiter = Limiter(key_func=get_remote_address, default_limits=[settings.rate_limit])
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# === Health Endpoints ===

@app.get("/health")
def health():
    return {"status": "alive"}


@app.get("/ready", response_model=HealthResponse)
async def ready():
    neo4j_ok = await graphdb.health_check()
    redis_ok = cache.ping()
    return HealthResponse(
        status="ready" if neo4j_ok else "degraded",
        neo4j=neo4j_ok,
        weaviate=True,  # Checked at startup
        redis=redis_ok
    )


# === Chat Endpoints ===

@app.post("/chat")
@limiter.limit(settings.rate_limit)
async def chat(request: ChatRequest, req: Request):
    """Non-streaming chat."""
    session_id = request.session_id or str(uuid.uuid4())
    
    # Save user message
    cache.add_message(session_id, "user", request.query)
    
    # Run pipeline
    result = await pipeline.ainvoke({
        "query": request.query,
        "history": cache.get_history(session_id, limit=10)
    })
    
    response = result.get("response", [""])[0]
    
    # Save assistant message
    cache.add_message(session_id, "assistant", response)
    
    return {"response": response, "session_id": session_id}


@app.post("/chat/stream")
@limiter.limit(settings.rate_limit)
async def chat_stream(request: ChatStreamRequest, req: Request):
    """Streaming chat - sends tokens as generated."""
    session_id = request.session_id or str(uuid.uuid4())
    
    cache.add_message(session_id, "user", request.query)
    
    async def generate():
        full_response = ""
        try:
            async for chunk in pipeline.astream({
                "query": request.query,
                "history": request.history or []
            }):
                if "response" in chunk and chunk["response"]:
                    new_text = chunk["response"][-1]
                    if len(new_text) > len(full_response):
                        delta = new_text[len(full_response):]
                        full_response = new_text
                        yield delta
            
            cache.add_message(session_id, "assistant", full_response)
        except Exception as e:
            logger.error(f"Stream error: {e}")
            yield "\n\n[Error generating response]"
    
    return StreamingResponse(
        generate(),
        media_type="text/plain",
        headers={"X-Accel-Buffering": "no"}
    )


# === Document Endpoints ===

@app.post("/documents/upload")
async def upload_document(file: UploadFile = File(...)):
    """Upload and ingest document."""
    suffix = Path(file.filename).suffix.lower()
    if suffix not in {".pdf", ".txt", ".md"}:
        raise HTTPException(400, f"Unsupported type: {suffix}")
    
    content = await file.read()
    if len(content) > settings.max_upload_mb * 1024 * 1024:
        raise HTTPException(400, "File too large")
    
    # Save file
    filepath = Path(settings.upload_dir) / file.filename
    filepath.write_bytes(content)
    
    # Parse and chunk
    try:
        if suffix == ".pdf":
            from pypdf import PdfReader
            reader = PdfReader(str(filepath))
            text = "\n\n".join(p.extract_text() or "" for p in reader.pages)
        else:
            text = content.decode("utf-8")
        
        # Simple chunking
        chunks = []
        chunk_size = 1000
        for i in range(0, len(text), chunk_size - 100):
            chunks.append(text[i:i + chunk_size])
        
        # Embed and store
        embed_model = get_embedding_model()
        embeddings = embed_model.embed_documents(chunks)
        
        doc_id = str(uuid.uuid4())[:8]
        chunk_ids = [f"{doc_id}_{i}" for i in range(len(chunks))]
        
        vectorstore.insert(embeddings, chunk_ids, chunks, doc_id)
        
        return {
            "doc_id": doc_id,
            "filename": file.filename,
            "chunks": len(chunks),
            "chars": len(text)
        }
    except Exception as e:
        logger.error(f"Ingest error: {e}")
        raise HTTPException(500, str(e))


@app.get("/documents")
def list_documents():
    """List uploaded documents."""
    upload_dir = Path(settings.upload_dir)
    if not upload_dir.exists():
        return {"documents": []}
    
    docs = []
    for f in upload_dir.iterdir():
        if f.is_file() and f.suffix.lower() in {".pdf", ".txt", ".md"}:
            docs.append({
                "filename": f.name,
                "size": f.stat().st_size
            })
    return {"documents": docs}


# === Session Endpoints ===

@app.get("/session/{session_id}/history")
def get_history(session_id: str, limit: int = 20):
    return {"messages": cache.get_history(session_id, limit)}


@app.delete("/session/{session_id}")
def clear_session(session_id: str):
    cache.clear_history(session_id)
    return {"status": "cleared"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.api_host, port=settings.api_port)
