"""Neo4j Graph Database"""
import logging
from typing import Optional
from neo4j import AsyncGraphDatabase, AsyncDriver

from graph_rag.config import settings

logger = logging.getLogger(__name__)


class GraphDB:
    _driver: Optional[AsyncDriver] = None
    
    @classmethod
    async def connect(cls) -> AsyncDriver:
        if cls._driver is None:
            cls._driver = AsyncGraphDatabase.driver(settings.neo4j_uri, auth=(settings.neo4j_user, settings.neo4j_password), max_connection_pool_size=50)
            logger.info("Neo4j connected")
        return cls._driver
    
    @classmethod
    async def close(cls):
        if cls._driver:
            await cls._driver.close()
            cls._driver = None
    
    @classmethod
    async def execute(cls, query: str, params: dict = None) -> list:
        driver = await cls.connect()
        async with driver.session() as session:
            result = await session.run(query, params or {})
            return [dict(record) async for record in result]
    
    @classmethod
    async def get_related_entities(cls, entity: str, hops: int = 2) -> list:
        query = """
        MATCH path = (e:Entity)-[*1..2]-(related)
        WHERE toLower(e.name) CONTAINS toLower($entity)
        RETURN e.name AS source, [r IN relationships(path) | type(r)] AS rels, related.name AS target
        LIMIT 20
        """
        return await cls.execute(query, {"entity": entity})
    
    @classmethod
    async def health_check(cls) -> bool:
        try:
            await cls.execute("RETURN 1")
            return True
        except:
            return False


graphdb = GraphDB
