"""
Weaviate Vector Store Service for GraphRAG.

Provides vector similarity search capabilities for the hybrid retrieval pipeline.
"""
import weaviate
from weaviate.classes.init import Auth
from weaviate.classes.config import Configure, Property, DataType
from weaviate.classes.query import MetadataQuery
from ..settings import settings
import logging
from typing import List, Optional

logger = logging.getLogger(__name__)


class WeaviateService:
    """
    Service for interacting with Weaviate vector store.
    """
    
    def __init__(self):
        self.class_name = settings.WEAVIATE_CLASS_NAME
        self._client: Optional[weaviate.WeaviateClient] = None
        self._connect()
        self._create_schema_if_not_exists()

    def _connect(self):
        """Connect to Weaviate."""
        try:
            logger.info(f"Connecting to Weaviate at {settings.WEAVIATE_HOST}:{settings.WEAVIATE_PORT}")
            self._client = weaviate.connect_to_local(
                host=settings.WEAVIATE_HOST,
                port=settings.WEAVIATE_PORT,
                grpc_port=settings.WEAVIATE_GRPC_PORT,
            )
            logger.info("Successfully connected to Weaviate.")
        except Exception as e:
            logger.error(f"Failed to connect to Weaviate: {e}")
            raise

    def _create_schema_if_not_exists(self):
        """Create the collection schema if it does not already exist."""
        try:
            if not self._client.collections.exists(self.class_name):
                logger.info(f"Collection '{self.class_name}' not found. Creating new collection.")
                
                self._client.collections.create(
                    name=self.class_name,
                    vectorizer_config=Configure.Vectorizer.none(),  # We provide our own vectors
                    properties=[
                        Property(
                            name="chunk_id",
                            data_type=DataType.TEXT,
                            description="Source document chunk identifier"
                        ),
                        Property(
                            name="content",
                            data_type=DataType.TEXT,
                            description="Text content of the chunk"
                        ),
                    ]
                )
                logger.info(f"Collection '{self.class_name}' created successfully.")
            else:
                logger.info(f"Collection '{self.class_name}' already exists.")
        except Exception as e:
            logger.error(f"Failed to create schema: {e}")
            raise

    @property
    def client(self) -> weaviate.WeaviateClient:
        """Get the Weaviate client instance."""
        if self._client is None:
            self._connect()
        return self._client

    def insert(self, vectors: List[List[float]], chunk_ids: List[str], contents: Optional[List[str]] = None):
        """
        Insert vectors into the collection.

        Args:
            vectors (List[List[float]]): A list of vector embeddings.
            chunk_ids (List[str]): A list of corresponding chunk IDs.
            contents (Optional[List[str]]): Optional list of text contents.
        """
        if not vectors:
            return None

        try:
            collection = self._client.collections.get(self.class_name)
            
            with collection.batch.dynamic() as batch:
                for i, (vector, chunk_id) in enumerate(zip(vectors, chunk_ids)):
                    properties = {
                        "chunk_id": chunk_id,
                        "content": contents[i] if contents and i < len(contents) else chunk_id
                    }
                    batch.add_object(
                        properties=properties,
                        vector=vector
                    )
            
            logger.info(f"Successfully inserted {len(vectors)} vectors into Weaviate.")
            return True
        except Exception as e:
            logger.error(f"Failed to insert vectors into Weaviate: {e}")
            raise

    def search(self, query_vector: List[float], top_k: int = 5) -> List[dict]:
        """
        Search for similar vectors in the collection.

        Args:
            query_vector (List[float]): The vector to search with.
            top_k (int): The number of similar results to return.

        Returns:
            list: A list of search results with chunk_id and distance.
        """
        try:
            collection = self._client.collections.get(self.class_name)
            
            response = collection.query.near_vector(
                near_vector=query_vector,
                limit=top_k,
                return_metadata=MetadataQuery(distance=True)
            )
            
            results = []
            for obj in response.objects:
                results.append({
                    "chunk_id": obj.properties.get("chunk_id"),
                    "content": obj.properties.get("content"),
                    "distance": obj.metadata.distance if obj.metadata else None
                })
            
            return results
        except Exception as e:
            logger.error(f"Failed to search in Weaviate: {e}")
            raise

    def close(self):
        """Close the Weaviate connection."""
        if self._client:
            self._client.close()
            logger.info("Weaviate connection closed.")


# Singleton instance for the service
_weaviate_service: Optional[WeaviateService] = None


def get_weaviate_service() -> WeaviateService:
    """FastAPI dependency to get the Weaviate service instance."""
    global _weaviate_service
    if _weaviate_service is None:
        _weaviate_service = WeaviateService()
    return _weaviate_service
