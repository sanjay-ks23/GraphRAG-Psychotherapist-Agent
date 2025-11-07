"""
Environment configuration and secrets management
"""
from __future__ import annotations

import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment"""
    
    # Application
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = False
    JWT_SECRET: str
    
    # OpenAI GPT-5
    OPENAI_API_KEY: str
    OPENAI_MODEL: str = "gpt-4-turbo-preview"  # Use gpt-5-turbo when available
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-large"
    OPENAI_MAX_TOKENS: int = 4096
    OPENAI_TEMPERATURE: float = 0.4
    
    # Milvus
    MILVUS_URI: str = "http://localhost:19530"
    MILVUS_COLLECTION: str = "therapy_embeddings"
    
    # Neo4j
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str
    
    # Redis
    REDIS_URI: str = "redis://localhost:6379"
    REDIS_TTL: int = 1800
    
    # Safety
    SAFETY_THRESHOLD_HIGH: float = 0.9
    SAFETY_THRESHOLD_MEDIUM: float = 0.7
    
    # MLflow
    MLFLOW_TRACKING_URI: str = "http://localhost:5000"
    
    # Escalation
    CLINICIAN_WEBHOOK_URL: str = ""
    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    TWILIO_FROM_PHONE: str = ""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True
    )


settings = Settings()
