"""
Matching Engine Module.

This module handles matching bank transactions with ledger transactions
using rule-based and embedding-based similarity.
"""

from .models import Match, MatchType, MatchResult
from .rules import RuleBasedMatcher, MatchingConfig
from .scorer import ConfidenceScorer

# Lazy import for embeddings (requires numpy, sentence-transformers, faiss)
try:
    from .embeddings import EmbeddingMatcher
    from .engine import MatchingEngine
    __all__ = [
        "Match",
        "MatchType",
        "MatchResult",
        "RuleBasedMatcher",
        "MatchingConfig",
        "EmbeddingMatcher",
        "ConfidenceScorer",
        "MatchingEngine",
    ]
except ImportError:
    # Embeddings not available, but rule-based matching still works
    __all__ = [
        "Match",
        "MatchType",
        "MatchResult",
        "RuleBasedMatcher",
        "MatchingConfig",
        "ConfidenceScorer",
    ]

