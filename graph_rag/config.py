"""
Centralized Configuration - 12-Factor App Style

All settings loaded from environment variables with sensible defaults.
"""
import os
from pydantic_settings import BaseSettings
from pydantic import Field
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # --- LLM ---
    model_provider: str = Field(default="aws_bedrock", alias="MODEL_PROVIDER")
    llm_model_id: str = Field(default="anthropic.claude-3-sonnet-20240229-v1:0", alias="LLM_MODEL_ID")
    embedding_model_id: str = Field(default="amazon.titan-embed-text-v2:0", alias="EMBEDDING_MODEL_ID")
    embedding_dim: int = Field(default=1024, alias="EMBEDDING_DIM")
    
    # --- AWS ---
    aws_region: str = Field(default="us-east-1", alias="AWS_REGION")
    aws_access_key_id: str | None = Field(default=None, alias="AWS_ACCESS_KEY_ID")
    aws_secret_access_key: str | None = Field(default=None, alias="AWS_SECRET_ACCESS_KEY")
    
    # --- OpenAI ---
    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    
    # --- Neo4j ---
    neo4j_uri: str = Field(default="bolt://localhost:7687", alias="NEO4J_URI")
    neo4j_user: str = Field(default="neo4j", alias="NEO4J_USER")
    neo4j_password: str = Field(default="password", alias="NEO4J_PASSWORD")
    
    # --- Weaviate ---
    weaviate_url: str = Field(default="http://localhost:8080", alias="WEAVIATE_URL")
    weaviate_class: str = Field(default="MentalWellnessDoc", alias="WEAVIATE_CLASS")
    
    # --- Redis ---
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")
    
    # --- API ---
    api_host: str = Field(default="0.0.0.0", alias="API_HOST")
    api_port: int = Field(default=8000, alias="API_PORT")
    rate_limit: str = Field(default="100/minute", alias="RATE_LIMIT")
    
    # --- Sessions ---
    session_ttl_hours: int = Field(default=24, alias="SESSION_TTL_HOURS")
    max_history: int = Field(default=50, alias="MAX_HISTORY")
    
    # --- Uploads ---
    upload_dir: str = Field(default="uploads", alias="UPLOAD_DIR")
    max_upload_mb: int = Field(default=10, alias="MAX_UPLOAD_MB")

    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance."""
    return Settings()


# Convenience export
settings = get_settings()
