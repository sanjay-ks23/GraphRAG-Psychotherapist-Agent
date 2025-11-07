"""OpenAI embedding service"""
from __future__ import annotations
from openai import OpenAI
from core.config import settings
from core.utils import get_logger

logger = get_logger(__name__)
client = OpenAI(api_key=settings.OPENAI_API_KEY)

class EmbeddingService:
    async def initialize(self):
        logger.info("Embedding service ready")
    
    async def embed_text(self, text: str) -> list[float]:
        response = client.embeddings.create(
            model=settings.OPENAI_EMBEDDING_MODEL,
            input=text
        )
        return response.data[0].embedding

embedding_service = EmbeddingService()
