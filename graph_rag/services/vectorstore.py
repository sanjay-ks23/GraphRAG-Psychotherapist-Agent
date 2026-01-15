"""
Vector Store Service - Weaviate integration.

Handles document embedding storage and semantic search.
"""
import logging
from typing import Optional
from functools import lru_cache
import weaviate
from weaviate.classes.config import Configure, Property, DataType

from graph_rag.config import settings

logger = logging.getLogger(__name__)


class VectorStore:
    """Weaviate vector store for document embeddings."""
    
    _client: Optional[weaviate.WeaviateClient] = None
    
    @classmethod
    def connect(cls) -> weaviate.WeaviateClient:
        """Get or create Weaviate connection."""
        if cls._client is None:
            url = settings.weaviate_url
            logger.info(f"Connecting to Weaviate: {url}")
            
            # Parse URL for host/port
            if url.startswith("http://"):
                url = url[7:]
            host, port = url.split(":") if ":" in url else (url, "8080")
            
            cls._client = weaviate.connect_to_local(
                host=host,
                port=int(port),
                grpc_port=50051
            )
            cls._ensure_collection()
            logger.info("Weaviate connected")
        return cls._client
    
    @classmethod
    def _ensure_collection(cls) -> None:
        """Create collection if not exists."""
        name = settings.weaviate_class
        try:
            if not cls._client.collections.exists(name):
                logger.info(f"Creating collection: {name}")
                cls._client.collections.create(
                    name=name,
                    vectorizer_config=Configure.Vectorizer.none(),
                    properties=[
                        Property(name="chunk_id", data_type=DataType.TEXT),
                        Property(name="content", data_type=DataType.TEXT),
                        Property(name="doc_id", data_type=DataType.TEXT),
                    ]
                )
        except Exception as e:
            # Handle race condition
            if "already exists" not in str(e).lower():
                raise
    
    @classmethod
    def insert(cls, vectors: list, chunk_ids: list, contents: list, doc_id: str = "") -> int:
        """Insert documents with embeddings."""
        client = cls.connect()
        collection = client.collections.get(settings.weaviate_class)
        
        with collection.batch.dynamic() as batch:
            for vec, cid, content in zip(vectors, chunk_ids, contents):
                batch.add_object(
                    vector=vec,
                    properties={
                        "chunk_id": cid,
                        "content": content,
                        "doc_id": doc_id
                    }
                )
        return len(vectors)
    
    @classmethod
    def search(cls, query_vector: list, top_k: int = 5) -> list:
        """Semantic search using vector similarity."""
        client = cls.connect()
        collection = client.collections.get(settings.weaviate_class)
        
        result = collection.query.near_vector(
            near_vector=query_vector,
            limit=top_k,
            return_properties=["chunk_id", "content", "doc_id"]
        )
        
        return [
            {
                "chunk_id": obj.properties.get("chunk_id", ""),
                "content": obj.properties.get("content", ""),
                "doc_id": obj.properties.get("doc_id", ""),
            }
            for obj in result.objects
        ]
    
    @classmethod
    def close(cls) -> None:
        """Close connection."""
        if cls._client:
            cls._client.close()
            cls._client = None


# Convenience alias
vectorstore = VectorStore
