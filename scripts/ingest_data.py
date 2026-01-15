"""
Data Ingestion Script

Ingests seed data from data/seed_kg.csv into Neo4j and Weaviate.
"""
import logging
import asyncio
import pandas as pd
from graph_rag.services import get_embedding_model, vectorstore, graphdb

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def ingest_data():
    logger.info("Starting ingestion...")

    # 1. Load Data
    try:
        df = pd.read_csv("data/seed_kg.csv")
        logger.info(f"Loaded {len(df)} rows")
    except FileNotFoundError:
        logger.error("data/seed_kg.csv not found")
        return

    # 2. Ingest into Neo4j
    logger.info("Ingesting to Neo4j...")
    await graphdb.connect()
    
    for _, row in df.iterrows():
        query = """
        MERGE (s:Entity {name: $source})
        MERGE (t:Entity {name: $target})
        MERGE (s)-[:RELATIONSHIP {type: $rel}]->(t)
        """
        await graphdb.execute(
            query, 
            {"source": row["source"], "target": row["target"], "rel": row["relationship"]}
        )
    
    logger.info("Neo4j ingestion complete")

    # 3. Ingest into Weaviate
    logger.info("Ingesting to Weaviate...")
    vectorstore.connect()
    
    # Embed unique entities
    entities = list(set(df["source"].tolist() + df["target"].tolist()))
    if entities:
        embeddings = get_embedding_model().embed_documents(entities)
        vectorstore.insert(
            vectors=embeddings,
            chunk_ids=entities,
            contents=entities,
            doc_id="seed_data"
        )
        logger.info(f"Inserted {len(entities)} entities to Weaviate")
    
    await graphdb.close()
    vectorstore.close()
    logger.info("Done!")

if __name__ == "__main__":
    asyncio.run(ingest_data())
