"""GraphRAG API Server"""
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

from graph_rag.config import settings
from graph_rag.models import ChatRequest, ChatStreamRequest, HealthResponse
from graph_rag.core import pipeline
from graph_rag.services import cache, vectorstore, graphdb, get_embedding_model

logging.basicConfig(level=logging.WARNING, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logging.getLogger("graph_rag").setLevel(logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting API...")
    try:
        vectorstore.connect()
    except Exception as e:
        logger.error(f"Weaviate failed: {e}")
    try:
        await graphdb.connect()
    except Exception as e:
        logger.error(f"Neo4j failed: {e}")
    os.makedirs(settings.upload_dir, exist_ok=True)
    yield
    vectorstore.close()
    await graphdb.close()


app = FastAPI(title="GraphRAG API", version="1.0.0", lifespan=lifespan)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

limiter = Limiter(key_func=get_remote_address, default_limits=[settings.rate_limit])
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/ready", response_model=HealthResponse)
async def ready():
    neo4j_ok = await graphdb.health_check()
    return HealthResponse(status="ready" if neo4j_ok else "degraded", neo4j=neo4j_ok, weaviate=True, redis=cache.ping())


@app.post("/chat")
@limiter.limit(settings.rate_limit)
async def chat(request: ChatRequest, req: Request):
    session_id = request.session_id or str(uuid.uuid4())
    cache.add_message(session_id, "user", request.query)
    
    result = await pipeline.ainvoke({
        "query": request.query,
        "history": cache.get_history(session_id, limit=10)
    })
    
    response = result.get("response", [""])[0]
    cache.add_message(session_id, "assistant", response)
    return {"response": response, "session_id": session_id}


@app.post("/chat/stream")
@limiter.limit(settings.rate_limit)
async def chat_stream(request: ChatStreamRequest, req: Request):
    session_id = request.session_id or str(uuid.uuid4())
    cache.add_message(session_id, "user", request.query)
    
    async def generate():
        full_response = ""
        try:
            async for chunk in pipeline.astream({"query": request.query, "history": request.history or []}):
                if "response" in chunk and chunk["response"]:
                    new_text = chunk["response"][-1]
                    if len(new_text) > len(full_response):
                        yield new_text[len(full_response):]
                        full_response = new_text
            cache.add_message(session_id, "assistant", full_response)
        except Exception as e:
            logger.error(f"Stream error: {e}")
            yield "\n\n[Error]"
    
    return StreamingResponse(generate(), media_type="text/plain", headers={"X-Accel-Buffering": "no"})


@app.post("/documents/upload")
async def upload_document(file: UploadFile = File(...)):
    suffix = Path(file.filename).suffix.lower()
    if suffix not in {".pdf", ".txt", ".md"}:
        raise HTTPException(400, f"Unsupported: {suffix}")
    
    content = await file.read()
    if len(content) > settings.max_upload_mb * 1024 * 1024:
        raise HTTPException(400, "File too large")
    
    filepath = Path(settings.upload_dir) / file.filename
    filepath.write_bytes(content)
    
    try:
        if suffix == ".pdf":
            from pypdf import PdfReader
            text = "\n\n".join(p.extract_text() or "" for p in PdfReader(str(filepath)).pages)
        else:
            text = content.decode("utf-8")
        
        chunks = [text[i:i+1000] for i in range(0, len(text), 900)]
        embeddings = get_embedding_model().embed_documents(chunks)
        doc_id = str(uuid.uuid4())[:8]
        vectorstore.insert(embeddings, [f"{doc_id}_{i}" for i in range(len(chunks))], chunks, doc_id)
        
        return {"doc_id": doc_id, "filename": file.filename, "chunks": len(chunks)}
    except Exception as e:
        logger.error(f"Ingest error: {e}")
        raise HTTPException(500, str(e))


@app.get("/documents")
def list_documents():
    upload_dir = Path(settings.upload_dir)
    if not upload_dir.exists():
        return {"documents": []}
    return {"documents": [{"filename": f.name, "size": f.stat().st_size} for f in upload_dir.iterdir() if f.suffix.lower() in {".pdf", ".txt", ".md"}]}


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
