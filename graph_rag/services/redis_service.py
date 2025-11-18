import redis
import json
from functools import wraps
from graph_rag.settings import settings

class RedisService:
    _client = None

    @classmethod
    def get_client(cls):
        if cls._client is None:
            cls._client = redis.Redis.from_url(settings.CELERY_BROKER_URL, decode_responses=True)
        return cls._client

    @classmethod
    def get(cls, key):
        client = cls.get_client()
        return client.get(key)

    @classmethod
    def set(cls, key, value, ex=3600):
        client = cls.get_client()
        client.set(key, value, ex=ex)

def cache_llm_response(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # Create a cache key based on the function name and arguments
        # This is a simple example; a more robust implementation might hash the arguments
        query = kwargs.get("query")
        if query:
            cache_key = f"llm_cache:{query}"
            cached_response = RedisService.get(cache_key)
            if cached_response:
                print(f"Cache hit for query: {query}")
                return json.loads(cached_response)

        # If not in cache, call the original function
        response = await func(*args, **kwargs)

        # Cache the response
        if query:
            RedisService.set(cache_key, json.dumps(response))
        return response
    return wrapper
