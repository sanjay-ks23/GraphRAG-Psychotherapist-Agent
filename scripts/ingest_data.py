import logging
import asyncio
import pandas as pd
from graph_rag.services.llm_service import get_embedding_model
from graph_rag.services.milvus_service import get_milvus_service
from graph_rag.services.neo4j_service import Neo4jService

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def ingest_data():
    """
    Main function to ingest data from a CSV file into Neo4j and Milvus.
    """
    logger.info("Starting data ingestion process...")

    # --- 1. Load Data ---
    try:
        df = pd.read_csv("data/seed_kg.csv")
        logger.info(f"Loaded {len(df)} rows from data/seed_kg.csv")
    except FileNotFoundError:
        logger.error("data/seed_kg.csv not found. Please ensure the seed data is in the 'data' directory.")
        return

    # --- 2. Initialize Services ---
    embedding_model = get_embedding_model()
    milvus_service = get_milvus_service()
    
    # --- 3. Ingest into Neo4j ---
    logger.info("Ingesting data into Neo4j...")
    # This is a simple example. A more robust implementation would handle
    # different node labels, properties, and relationships dynamically.
    for _, row in df.iterrows():
        # Create a simple graph from the CSV (assuming 'source', 'target', 'relationship' columns)
        cypher_query = """
        MERGE (s:Entity {name: $source})
        MERGE (t:Entity {name: $target})
        MERGE (s)-[:RELATIONSHIP {type: $rel}]->(t)
        """
        await Neo4jService.execute_query(
            cypher_query,
            parameters={"source": row["source"], "target": row["target"], "rel": row["relationship"]}
        )
    logger.info("Finished ingesting data into Neo4j.")

    # --- 4. Ingest into Milvus ---
    logger.info("Ingesting data into Milvus...")
    # We will create embeddings for the 'source' nodes as an example
    texts_to_embed = df["source"].unique().tolist()
    
    if texts_to_embed:
        embeddings = embedding_model.embed_documents(texts_to_embed)
        
        # The chunk_id can be the text itself or a more stable identifier
        chunk_ids = texts_to_embed
        
        milvus_service.insert(vectors=embeddings, chunk_ids=chunk_ids)
        logger.info(f"Successfully inserted {len(embeddings)} embeddings into Milvus.")
    else:
        logger.warning("No unique texts to embed for Milvus.")

    logger.info("Data ingestion process completed.")

if __name__ == "__main__":
    # Ensure the Neo4j driver is initialized before running
    async def main():
        await Neo4jService.get_driver()
        await ingest_data()
        await Neo4jService.close_driver()

    asyncio.run(main())
