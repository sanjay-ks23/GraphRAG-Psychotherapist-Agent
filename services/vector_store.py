"""Milvus vector store client"""
from __future__ import annotations
from pymilvus import connections, Collection
from core.config import settings
from core.utils import get_logger

logger = get_logger(__name__)

class VectorStore:
    def __init__(self):
        self.collection = None
    
    async def connect(self):
        connections.connect("default", uri=settings.MILVUS_URI)
        self.collection = Collection(settings.MILVUS_COLLECTION)
        logger.info("Connected to Milvus")
    
    async def disconnect(self):
        connections.disconnect("default")
    
    async def search(self, embedding: list[float], top_k: int, filters: dict = None) -> list[dict]:
        if not self.collection:
            return []
        results = self.collection.search(
            data=[embedding],
            anns_field="embedding",
            param={"metric_type": "L2", "params": {"nprobe": 10}},
            limit=top_k
        )
        return [{"id": r.id, "score": r.distance, "text": r.entity.get("text", "")} for r in results[0]]

vector_store = VectorStore()
