"""
Redis Cache Service - Sessions, LLM cache, embeddings cache.

Designed for horizontal scaling with stateless API pods.
"""
import json
import hashlib
import logging
from typing import Any, Optional
from datetime import datetime
from functools import lru_cache
import redis

from graph_rag.config import settings

logger = logging.getLogger(__name__)


class CacheService:
    """Redis-backed caching and session management."""
    
    _pool: Optional[redis.ConnectionPool] = None
    
    @classmethod
    def _get_pool(cls) -> redis.ConnectionPool:
        """Get connection pool (lazy init)."""
        if cls._pool is None:
            cls._pool = redis.ConnectionPool.from_url(
                settings.redis_url,
                decode_responses=True,
                max_connections=20
            )
        return cls._pool
    
    @classmethod
    def _client(cls) -> redis.Redis:
        """Get Redis client from pool."""
        return redis.Redis(connection_pool=cls._get_pool())
    
    @classmethod
    def ping(cls) -> bool:
        """Check Redis connectivity."""
        try:
            return cls._client().ping()
        except Exception as e:
            logger.warning(f"Redis unavailable: {e}")
            return False
    
    # === Generic Cache ===
    
    @classmethod
    def get(cls, key: str) -> Optional[str]:
        try:
            return cls._client().get(key)
        except Exception:
            return None
    
    @classmethod
    def set(cls, key: str, value: str, ttl: int = 3600) -> bool:
        try:
            cls._client().set(key, value, ex=ttl)
            return True
        except Exception:
            return False
    
    @classmethod
    def delete(cls, key: str) -> bool:
        try:
            cls._client().delete(key)
            return True
        except Exception:
            return False
    
    # === LLM Response Cache ===
    
    @classmethod
    def _llm_key(cls, query: str) -> str:
        h = hashlib.md5(query.encode()).hexdigest()[:12]
        return f"llm:{h}"
    
    @classmethod
    def get_cached_response(cls, query: str) -> Optional[str]:
        return cls.get(cls._llm_key(query))
    
    @classmethod
    def cache_response(cls, query: str, response: str, ttl: int = 1800) -> bool:
        return cls.set(cls._llm_key(query), response, ttl)
    
    # === Embedding Cache ===
    
    @classmethod
    def _embed_key(cls, text: str) -> str:
        h = hashlib.md5(text.encode()).hexdigest()[:12]
        return f"emb:{h}"
    
    @classmethod
    def get_cached_embedding(cls, text: str) -> Optional[list]:
        data = cls.get(cls._embed_key(text))
        return json.loads(data) if data else None
    
    @classmethod
    def cache_embedding(cls, text: str, embedding: list, ttl: int = 86400) -> bool:
        return cls.set(cls._embed_key(text), json.dumps(embedding), ttl)
    
    # === Session Management ===
    
    @classmethod
    def _session_key(cls, session_id: str) -> str:
        return f"session:{session_id}"
    
    @classmethod
    def _history_key(cls, session_id: str) -> str:
        return f"history:{session_id}"
    
    @classmethod
    def get_session(cls, session_id: str) -> Optional[dict]:
        data = cls.get(cls._session_key(session_id))
        return json.loads(data) if data else None
    
    @classmethod
    def save_session(cls, session_id: str, data: dict) -> bool:
        data["updated_at"] = datetime.utcnow().isoformat()
        ttl = settings.session_ttl_hours * 3600
        return cls.set(cls._session_key(session_id), json.dumps(data), ttl)
    
    @classmethod
    def add_message(cls, session_id: str, role: str, content: str) -> bool:
        try:
            client = cls._client()
            key = cls._history_key(session_id)
            msg = json.dumps({
                "role": role,
                "content": content,
                "ts": datetime.utcnow().isoformat()
            })
            client.rpush(key, msg)
            client.ltrim(key, -settings.max_history, -1)
            client.expire(key, settings.session_ttl_hours * 3600)
            return True
        except Exception:
            return False
    
    @classmethod
    def get_history(cls, session_id: str, limit: int = 20) -> list:
        try:
            key = cls._history_key(session_id)
            msgs = cls._client().lrange(key, -limit, -1)
            return [json.loads(m) for m in msgs]
        except Exception:
            return []
    
    @classmethod
    def clear_history(cls, session_id: str) -> bool:
        try:
            cls._client().delete(cls._history_key(session_id))
            return True
        except Exception:
            return False


# Convenience alias
cache = CacheService
