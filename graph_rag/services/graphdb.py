"""
Graph Database Service - Neo4j integration.

Handles knowledge graph queries and entity relationships.
"""
import logging
from typing import Optional, Any
from contextlib import asynccontextmanager
from neo4j import AsyncGraphDatabase, AsyncDriver

from graph_rag.config import settings

logger = logging.getLogger(__name__)


class GraphDB:
    """Neo4j graph database for knowledge graph operations."""
    
    _driver: Optional[AsyncDriver] = None
    
    @classmethod
    async def connect(cls) -> AsyncDriver:
        """Get or create Neo4j connection."""
        if cls._driver is None:
            logger.info(f"Connecting to Neo4j: {settings.neo4j_uri}")
            cls._driver = AsyncGraphDatabase.driver(
                settings.neo4j_uri,
                auth=(settings.neo4j_user, settings.neo4j_password),
                max_connection_pool_size=50
            )
            logger.info("Neo4j connected")
        return cls._driver
    
    @classmethod
    async def close(cls) -> None:
        """Close connection."""
        if cls._driver:
            await cls._driver.close()
            cls._driver = None
    
    @classmethod
    async def execute(cls, query: str, params: dict = None) -> list:
        """Execute Cypher query and return results."""
        driver = await cls.connect()
        async with driver.session() as session:
            result = await session.run(query, params or {})
            return [dict(record) async for record in result]
    
    @classmethod
    async def get_related_entities(cls, entity: str, hops: int = 2) -> list:
        """Find entities related to given entity."""
        query = """
        MATCH path = (e:Entity)-[*1..2]-(related)
        WHERE toLower(e.name) CONTAINS toLower($entity)
        RETURN e.name AS source,
               [r IN relationships(path) | type(r)] AS rels,
               related.name AS target
        LIMIT 20
        """
        return await cls.execute(query, {"entity": entity})
    
    @classmethod
    async def search_by_topic(cls, topic: str) -> list:
        """Search entities by topic/keyword."""
        query = """
        MATCH (e:Entity)
        WHERE toLower(e.name) CONTAINS toLower($topic)
           OR toLower(e.description) CONTAINS toLower($topic)
        RETURN e.name AS name, e.description AS description
        LIMIT 10
        """
        return await cls.execute(query, {"topic": topic})
    
    @classmethod
    async def health_check(cls) -> bool:
        """Check Neo4j connectivity."""
        try:
            await cls.execute("RETURN 1")
            return True
        except Exception as e:
            logger.warning(f"Neo4j health check failed: {e}")
            return False


# Convenience alias
graphdb = GraphDB
