"""
Application constants and model parameters
"""
from __future__ import annotations

# Pipeline timeouts (seconds)
TIMEOUT_RETRIEVAL = 3
TIMEOUT_LLM = 10
TIMEOUT_GRAPH_EXPANSION = 2

# Retrieval parameters
VECTOR_TOP_K = 24
GRAPH_MAX_HOPS = 2
GRAPH_MAX_NODES = 200

# Hybrid scoring weights
WEIGHT_VECTOR = 0.6
WEIGHT_GRAPH = 0.3
WEIGHT_NODE_SIM = 0.1

# Context assembly
MAX_CONTEXT_SNIPPETS = 6
MAX_CONTEXT_FACTS = 12
MAX_CONTEXT_TOKENS = 1800

# Safety keywords
CRITICAL_KEYWORDS = [
    "suicide", "kill myself", "end my life", "self harm",
    "hurt myself", "want to die", "no reason to live"
]

HIGH_RISK_KEYWORDS = [
    "depressed", "hopeless", "worthless", "alone",
    "scared", "afraid", "anxious", "panic"
]

# Session
SESSION_EXPIRY_MINUTES = 60
MAX_MESSAGE_LENGTH = 2000

# Supported languages
SUPPORTED_LANGUAGES = ["en", "hi", "ta", "te", "bn", "mr", "gu"]

# Age ranges
AGE_RANGES = ["6-8", "8-12", "12-16", "16-18"]
