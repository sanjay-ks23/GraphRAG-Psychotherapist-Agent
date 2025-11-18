from pymilvus import (
    connections,
    utility,
    Collection,
    CollectionSchema,
    FieldSchema,
    DataType,
)
from ..settings import settings
import logging
from typing import List

logger = logging.getLogger(__name__)

class MilvusService:
    """
    Service for interacting with Milvus vector store.
    """
    def __init__(self):
        self.collection_name = settings.MILVUS_COLLECTION
        self._connect()
        self._create_collection_if_not_exists()

    def _connect(self):
        """Connect to Milvus."""
        try:
            logger.info(f"Connecting to Milvus at {settings.MILVUS_HOST}:{settings.MILVUS_PORT}")
            connections.connect("default", host=settings.MILVUS_HOST, port=settings.MILVUS_PORT)
            logger.info("Successfully connected to Milvus.")
        except Exception as e:
            logger.error(f"Failed to connect to Milvus: {e}")
            raise

    def _create_collection_if_not_exists(self):
        """Create the collection if it does not already exist."""
        if not utility.has_collection(self.collection_name):
            logger.info(f"Collection '{self.collection_name}' not found. Creating new collection.")
            
            # Define fields for the collection
            # The primary key
            id_field = FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True)
            # The vector embedding
            embedding_field = FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=settings.EMBEDDING_DIM)
            # Source document chunk ID
            chunk_id_field = FieldSchema(name="chunk_id", dtype=DataType.VARCHAR, max_length=256)

            schema = CollectionSchema(
                fields=[id_field, embedding_field, chunk_id_field],
                description="Graph RAG document chunks",
                enable_dynamic_field=False
            )
            
            self.collection = Collection(self.collection_name, schema)
            
            logger.info(f"Collection '{self.collection_name}' created.")
            
            # Create an index for the embedding field for efficient search
            index_params = {
                "metric_type": "L2",
                "index_type": "IVF_FLAT",
                "params": {"nlist": 128},
            }
            self.collection.create_index("embedding", index_params)
            logger.info("Index created for 'embedding' field.")
        else:
            logger.info(f"Collection '{self.collection_name}' already exists.")
            self.collection = Collection(self.collection_name)
        
        self.collection.load()

    def insert(self, vectors: List[List[float]], chunk_ids: List[str]):
        """
        Insert vectors into the collection.

        Args:
            vectors (List[List[float]]): A list of vector embeddings.
            chunk_ids (List[str]): A list of corresponding chunk IDs.
        """
        if not vectors:
            return None
        
        entities = [
            vectors,
            chunk_ids
        ]
        
        try:
            result = self.collection.insert(entities)
            self.collection.flush()
            logger.info(f"Successfully inserted {len(vectors)} vectors.")
            return result
        except Exception as e:
            logger.error(f"Failed to insert vectors into Milvus: {e}")
            raise

    def search(self, query_vector: List[float], top_k: int = 5):
        """
        Search for similar vectors in the collection.

        Args:
            query_vector (List[float]): The vector to search with.
            top_k (int): The number of similar results to return.

        Returns:
            list: A list of search results.
        """
        search_params = {"metric_type": "L2", "params": {"nprobe": 10}}
        
        try:
            results = self.collection.search(
                data=[query_vector],
                anns_field="embedding",
                param=search_params,
                limit=top_k,
                output_fields=["chunk_id"]
            )
            return results
        except Exception as e:
            logger.error(f"Failed to search in Milvus: {e}")
            raise

# Singleton instance for the service
milvus_service = MilvusService()

# Dependency for FastAPI
def get_milvus_service() -> MilvusService:
    """FastAPI dependency to get the Milvus service instance."""
    return milvus_service
