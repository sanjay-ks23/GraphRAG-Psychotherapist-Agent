from ..settings import settings
import logging
from langchain_aws import ChatBedrock
from langchain_openai import ChatOpenAI
from langchain_community.embeddings import BedrockEmbeddings
from langchain_openai import OpenAIEmbeddings
from langchain.schema.language_model import BaseLanguageModel
from langchain.embeddings.base import Embeddings

logger = logging.getLogger(__name__)

class LLMService:
    """
    Service to provide LLM and Embedding model instances based on configuration.
    """
    _chat_model: BaseLanguageModel | None = None
    _embedding_model: Embeddings | None = None

    @classmethod
    def get_chat_model(cls) -> BaseLanguageModel:
        """
        Returns a singleton instance of the chat model.
        """
        if cls._chat_model is None:
            logger.info(f"Initializing chat model for provider: {settings.MODEL_PROVIDER}")
            if settings.MODEL_PROVIDER == "aws_bedrock":
                cls._chat_model = ChatBedrock(
                    model_id=settings.LLM_MODEL_ID,
                    client=None,  # Boto3 will use default credentials
                    model_kwargs={"temperature": 0.1},
                    streaming=True,
                    region_name=settings.AWS_REGION
                )
            elif settings.MODEL_PROVIDER == "openai":
                if not settings.OPENAI_API_KEY:
                    raise ValueError("OPENAI_API_KEY must be set for OpenAI provider")
                cls._chat_model = ChatOpenAI(
                    api_key=settings.OPENAI_API_KEY,
                    model=settings.LLM_MODEL_ID,
                    temperature=0,
                    streaming=True
                )
            else:
                raise ValueError(f"Unsupported model provider: {settings.MODEL_PROVIDER}")
            logger.info("Chat model initialized successfully.")
        return cls._chat_model

    @classmethod
    def get_embedding_model(cls) -> Embeddings:
        """
        Returns a singleton instance of the embedding model.
        """
        if cls._embedding_model is None:
            logger.info(f"Initializing embedding model for provider: {settings.MODEL_PROVIDER}")
            if settings.MODEL_PROVIDER == "aws_bedrock":
                cls._embedding_model = BedrockEmbeddings(
                    client=None, # Boto3 will use default credentials
                    model_id=settings.EMBEDDING_MODEL_ID,
                    region_name=settings.AWS_REGION
                )
            elif settings.MODEL_PROVIDER == "openai":
                if not settings.OPENAI_API_KEY:
                    raise ValueError("OPENAI_API_KEY must be set for OpenAI provider")
                cls._embedding_model = OpenAIEmbeddings(
                    api_key=settings.OPENAI_API_KEY,
                    model=settings.EMBEDDING_MODEL_ID
                )
            else:
                raise ValueError(f"Unsupported model provider: {settings.MODEL_PROVIDER}")
            logger.info("Embedding model initialized successfully.")
        return cls._embedding_model

# FastAPI dependencies
def get_llm_service() -> LLMService:
    """FastAPI dependency to get the LLM service."""
    return LLMService

def get_chat_model() -> BaseLanguageModel:
    """FastAPI dependency to get the chat model instance."""
    return LLMService.get_chat_model()

def get_embedding_model() -> Embeddings:
    """FastAPI dependency to get the embedding model instance."""
    return LLMService.get_embedding_model()
