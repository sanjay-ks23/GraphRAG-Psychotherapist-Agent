from neo4j import AsyncGraphDatabase, AsyncDriver
from ..settings import settings
import logging

logger = logging.getLogger(__name__)

class Neo4jService:
    """
    Service to interact with the Neo4j database.
    Manages the database driver and provides methods for executing queries.
    """
    _driver: AsyncDriver | None = None

    @classmethod
    async def get_driver(cls) -> AsyncDriver:
        """
        Initializes and returns a singleton Neo4j driver instance.
        """
        if cls._driver is None:
            logger.info("Initializing Neo4j driver...")
            try:
                cls._driver = AsyncGraphDatabase.driver(
                    settings.NEO4J_URI,
                    auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
                )
                await cls._driver.verify_connectivity()
                logger.info("Neo4j driver initialized successfully.")
            except Exception as e:
                logger.error(f"Failed to initialize Neo4j driver: {e}")
                raise
        return cls._driver

    @classmethod
    async def close_driver(cls):
        """
        Closes the Neo4j driver connection.
        """
        if cls._driver:
            logger.info("Closing Neo4j driver.")
            await cls._driver.close()
            cls._driver = None

    @classmethod
    async def execute_query(cls, query: str, parameters: dict | None = None):
        """
        Executes a Cypher query against the database.

        Args:
            query (str): The Cypher query to execute.
            parameters (dict, optional): Parameters for the query.

        Returns:
            list: A list of records from the query result.
        """
        driver = await cls.get_driver()
        try:
            records, _, _ = await driver.execute_query(
                query,
                parameters or {},
                database_=settings.NEO4J_DATABASE
            )
            return records
        except Exception as e:
            logger.error(f"Error executing Neo4j query: {e}")
            # In a production scenario, you might want to handle different exceptions
            # differently, e.g., connection errors vs. query syntax errors.
            raise

# Dependency for FastAPI
async def get_neo4j_service() -> Neo4jService:
    """
    FastAPI dependency to get the Neo4j service.
    Ensures the driver is initialized and properly closed.
    """
    await Neo4jService.get_driver()
    yield Neo4jService
    # The closing logic can be handled by a FastAPI event handler
    # for application shutdown to be more robust.
