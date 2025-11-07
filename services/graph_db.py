"""Neo4j knowledge graph client"""
from __future__ import annotations
from neo4j import AsyncGraphDatabase
from core.config import settings
from core.utils import get_logger

logger = get_logger(__name__)

class GraphDB:
    def __init__(self):
        self.driver = None
    
    async def connect(self):
        self.driver = AsyncGraphDatabase.driver(
            settings.NEO4J_URI,
            auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
        )
        logger.info("Connected to Neo4j")
    
    async def disconnect(self):
        if self.driver:
            await self.driver.close()
    
    async def find_seed_nodes(self, text: str, language: str) -> list[dict]:
        if not self.driver:
            return []
        async with self.driver.session() as session:
            result = await session.run(
                "MATCH (n) WHERE n.language = $lang RETURN n LIMIT 5",
                lang=language
            )
            return [{"id": r["n"].id, "type": r["n"].get("type")} async for r in result]
    
    async def expand_graph(self, seed_ids: list, max_hops: int, max_nodes: int) -> list[dict]:
        if not self.driver or not seed_ids:
            return []
        async with self.driver.session() as session:
            result = await session.run(
                "MATCH (n)-[r*1..2]-(m) WHERE id(n) IN $ids RETURN m LIMIT $limit",
                ids=seed_ids, limit=max_nodes
            )
            return [{"id": r["m"].id, "text": r["m"].get("text", ""), "score": 0.5} async for r in result]

graph_db = GraphDB()
