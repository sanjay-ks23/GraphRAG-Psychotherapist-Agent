"""LLM Service"""
import logging
from functools import lru_cache
from langchain_core.language_models import BaseChatModel
from langchain_core.embeddings import Embeddings
from langchain_aws import ChatBedrock, BedrockEmbeddings
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from graph_rag.config import settings

logger = logging.getLogger(__name__)


@lru_cache
def get_chat_model() -> BaseChatModel:
    if settings.model_provider == "aws_bedrock":
        return ChatBedrock(
            model_id=settings.llm_model_id,
            model_kwargs={"temperature": 0.1},
            streaming=True,
            region_name=settings.aws_region
        )
    elif settings.model_provider == "openai":
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY required")
        return ChatOpenAI(
            api_key=settings.openai_api_key,
            model=settings.llm_model_id,
            temperature=0,
            streaming=True
        )
    raise ValueError(f"Unknown provider: {settings.model_provider}")


@lru_cache
def get_embedding_model() -> Embeddings:
    if settings.model_provider == "aws_bedrock":
        return BedrockEmbeddings(model_id=settings.embedding_model_id, region_name=settings.aws_region)
    elif settings.model_provider == "openai":
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY required")
        return OpenAIEmbeddings(api_key=settings.openai_api_key, model=settings.embedding_model_id)
    raise ValueError(f"Unknown provider: {settings.model_provider}")
