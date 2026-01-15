"""Weaviate Vector Store"""
import logging
from typing import Optional
import weaviate
from weaviate.classes.config import Configure, Property, DataType

from graph_rag.config import settings

logger = logging.getLogger(__name__)


class VectorStore:
    _client: Optional[weaviate.WeaviateClient] = None
    
    @classmethod
    def connect(cls) -> weaviate.WeaviateClient:
        if cls._client is None:
            url = settings.weaviate_url.replace("http://", "")
            host, port = url.split(":") if ":" in url else (url, "8080")
            cls._client = weaviate.connect_to_local(host=host, port=int(port), grpc_port=50051)
            cls._ensure_collection()
            logger.info("Weaviate connected")
        return cls._client
    
    @classmethod
    def _ensure_collection(cls):
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
            if "already exists" not in str(e).lower():
                raise
    
    @classmethod
    def insert(cls, vectors: list, chunk_ids: list, contents: list, doc_id: str = "") -> int:
        collection = cls.connect().collections.get(settings.weaviate_class)
        with collection.batch.dynamic() as batch:
            for vec, cid, content in zip(vectors, chunk_ids, contents):
                batch.add_object(vector=vec, properties={"chunk_id": cid, "content": content, "doc_id": doc_id})
        return len(vectors)
    
    @classmethod
    def search(cls, query_vector: list, top_k: int = 5) -> list:
        collection = cls.connect().collections.get(settings.weaviate_class)
        result = collection.query.near_vector(near_vector=query_vector, limit=top_k, return_properties=["chunk_id", "content", "doc_id"])
        return [{"chunk_id": o.properties.get("chunk_id", ""), "content": o.properties.get("content", ""), "doc_id": o.properties.get("doc_id", "")} for o in result.objects]
    
    @classmethod
    def close(cls):
        if cls._client:
            cls._client.close()
            cls._client = None


vectorstore = VectorStore
