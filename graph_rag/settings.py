import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

# Load .env file in local development
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')

class Settings(BaseSettings):
    """
    Centralized application settings.
    """
    model_config = SettingsConfigDict(env_file=dotenv_path, env_file_encoding='utf-8', extra='ignore')

    # --- LLM and Embedding Model Configuration ---
    # Using a generic model name that can be mapped to different providers.
    # For AWS Bedrock, this could be 'anthropic.claude-3-sonnet-20240229-v1:0'
    # For OpenAI, this could be 'gpt-4o'
    LLM_MODEL_ID: str = Field(default="anthropic.claude-3-sonnet-20240229-v1:0", description="LLM model ID for generation.")
    # For AWS Bedrock, this could be 'amazon.titan-embed-text-v2:0'
    # For OpenAI, this could be 'text-embedding-3-large'
    EMBEDDING_MODEL_ID: str = Field(default="amazon.titan-embed-text-v2:0", description="Embedding model ID.")
    # The provider for the models, e.g., 'aws_bedrock' or 'openai'
    MODEL_PROVIDER: str = Field(default="aws_bedrock", description="The provider for the LLM and embedding models.")


    # --- AWS Configuration (if MODEL_PROVIDER is 'aws_bedrock') ---
    AWS_REGION: str = Field(default="us-east-1", description="AWS region for Bedrock and other services.")
    AWS_ACCESS_KEY_ID: str | None = Field(default=None, description="AWS access key ID.")
    AWS_SECRET_ACCESS_KEY: str | None = Field(default=None, description="AWS secret access key.")

    # --- OpenAI Configuration (if MODEL_PROVIDER is 'openai') ---
    OPENAI_API_KEY: str | None = Field(default=None, description="OpenAI API key.")

    # --- Neo4j Database Configuration ---
    NEO4J_URI: str = Field(default="bolt://localhost:7687", description="Neo4j connection URI.")
    NEO4J_USER: str = Field(default="neo4j", description="Neo4j username.")
    NEO4J_PASSWORD: str = Field(default="password", description="Neo4j password.")
    NEO4J_DATABASE: str = Field(default="neo4j", description="Neo4j database name.")

    # --- Weaviate Vector Store Configuration ---
    WEAVIATE_HOST: str = Field(default="localhost", description="Weaviate host.")
    WEAVIATE_PORT: int = Field(default=8080, description="Weaviate HTTP port.")
    WEAVIATE_GRPC_PORT: int = Field(default=50051, description="Weaviate gRPC port.")
    WEAVIATE_CLASS_NAME: str = Field(default="GraphRAGDocument", description="Weaviate class name.")
    EMBEDDING_DIM: int = Field(default=1024, description="Dimension of the embedding model.")

    # --- API Server Configuration ---
    API_HOST: str = Field(default="0.0.0.0", description="Host for the API server.")
    API_PORT: int = Field(default=8000, description="Port for the API server.")
    RATE_LIMIT: str = Field(default="100/minute", description="Rate limit for API requests.")

    # --- Celery Configuration ---
    CELERY_BROKER_URL: str = Field(default="redis://localhost:6379/0", description="Celery broker URL.")
    CELERY_RESULT_BACKEND: str = Field(default="redis://localhost:6379/0", description="Celery result backend URL.")


# Instantiate the settings
settings = Settings()
