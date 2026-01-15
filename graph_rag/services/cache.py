"""Redis Cache Service"""
import json
import hashlib
import logging
from typing import Optional
from datetime import datetime
import redis

from graph_rag.config import settings

logger = logging.getLogger(__name__)


class CacheService:
    _pool = None
    
    @classmethod
    def _get_pool(cls):
        if cls._pool is None:
            cls._pool = redis.ConnectionPool.from_url(settings.redis_url, decode_responses=True, max_connections=20)
        return cls._pool
    
    @classmethod
    def _client(cls):
        return redis.Redis(connection_pool=cls._get_pool())
    
    @classmethod
    def ping(cls) -> bool:
        try:
            return cls._client().ping()
        except:
            return False
    
    @classmethod
    def get(cls, key: str) -> Optional[str]:
        try:
            return cls._client().get(key)
        except:
            return None
    
    @classmethod
    def set(cls, key: str, value: str, ttl: int = 3600) -> bool:
        try:
            cls._client().set(key, value, ex=ttl)
            return True
        except:
            return False
    
    @classmethod
    def _llm_key(cls, q: str) -> str:
        return f"llm:{hashlib.md5(q.encode()).hexdigest()[:12]}"
    
    @classmethod
    def get_cached_response(cls, q: str) -> Optional[str]:
        return cls.get(cls._llm_key(q))
    
    @classmethod
    def cache_response(cls, q: str, r: str, ttl: int = 1800) -> bool:
        return cls.set(cls._llm_key(q), r, ttl)
    
    @classmethod
    def _embed_key(cls, t: str) -> str:
        return f"emb:{hashlib.md5(t.encode()).hexdigest()[:12]}"
    
    @classmethod
    def get_cached_embedding(cls, t: str) -> Optional[list]:
        d = cls.get(cls._embed_key(t))
        return json.loads(d) if d else None
    
    @classmethod
    def cache_embedding(cls, t: str, e: list, ttl: int = 86400) -> bool:
        return cls.set(cls._embed_key(t), json.dumps(e), ttl)
    
    @classmethod
    def add_message(cls, sid: str, role: str, content: str) -> bool:
        try:
            c = cls._client()
            key = f"history:{sid}"
            c.rpush(key, json.dumps({"role": role, "content": content, "ts": datetime.utcnow().isoformat()}))
            c.ltrim(key, -settings.max_history, -1)
            c.expire(key, settings.session_ttl_hours * 3600)
            return True
        except:
            return False
    
    @classmethod
    def get_history(cls, sid: str, limit: int = 20) -> list:
        try:
            return [json.loads(m) for m in cls._client().lrange(f"history:{sid}", -limit, -1)]
        except:
            return []
    
    @classmethod
    def clear_history(cls, sid: str) -> bool:
        try:
            cls._client().delete(f"history:{sid}")
            return True
        except:
            return False


cache = CacheService
