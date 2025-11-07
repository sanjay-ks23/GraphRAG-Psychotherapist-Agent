"""
Generic utility functions for logging, tracing, and helpers
"""
from __future__ import annotations

import logging
import sys
import time
import uuid
from typing import Any
from functools import wraps


def setup_logging(level: str = "INFO") -> None:
    """Configure application logging"""
    logging.basicConfig(
        level=getattr(logging, level),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)]
    )


def get_logger(name: str) -> logging.Logger:
    """Get logger instance"""
    return logging.getLogger(name)


def generate_id(prefix: str = "") -> str:
    """Generate unique ID with optional prefix"""
    return f"{prefix}_{uuid.uuid4().hex[:16]}" if prefix else uuid.uuid4().hex


def timing_decorator(func):
    """Decorator to measure function execution time"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start = time.time()
        result = await func(*args, **kwargs)
        duration = time.time() - start
        logger = get_logger(func.__module__)
        logger.info(f"{func.__name__} took {duration:.3f}s")
        return result
    return wrapper


def sanitize_input(text: str) -> str:
    """Basic input sanitization"""
    return text.strip()[:2000]


def format_provenance(sources: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Format provenance sources for response"""
    return [
        {
            "source_id": s.get("id"),
            "type": s.get("type"),
            "score": round(s.get("score", 0), 3),
            "snippet": s.get("text", "")[:200]
        }
        for s in sources
    ]
