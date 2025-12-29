"""
Models for matching results.
"""

from dataclasses import dataclass
from decimal import Decimal
from datetime import date
from typing import Optional
from enum import Enum


class MatchType(str, Enum):
    """Type of match."""
    EXACT = "exact"           # Perfect match on all criteria
    FUZZY = "fuzzy"           # Rule-based match (amount/date within tolerance)
    SEMANTIC = "semantic"      # Embedding-based match
    COMBINED = "combined"      # Combination of multiple signals


@dataclass
class Match:
    """Represents a match between two transactions."""
    bank_transaction_id: str
    ledger_transaction_id: str
    
    confidence: float  # 0.0 to 1.0
    
    match_type: MatchType
    
    # Match details
    amount_difference: Decimal
    date_difference_days: int
    description_similarity: float  # 0.0 to 1.0
    reference_match: bool
    
    # Match signals (for explainability)
    amount_score: float
    date_score: float
    description_score: float
    reference_score: float
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "bank_transaction_id": self.bank_transaction_id,
            "ledger_transaction_id": self.ledger_transaction_id,
            "confidence": self.confidence,
            "match_type": self.match_type.value,
            "amount_difference": str(self.amount_difference),
            "date_difference_days": self.date_difference_days,
            "description_similarity": self.description_similarity,
            "reference_match": self.reference_match,
            "amount_score": self.amount_score,
            "date_score": self.date_score,
            "description_score": self.description_score,
            "reference_score": self.reference_score,
        }


@dataclass
class MatchResult:
    """Result of matching operation."""
    matches: list[Match]
    unmatched_bank: list[str]  # Bank transaction IDs
    unmatched_ledger: list[str]  # Ledger transaction IDs
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "matches": [m.to_dict() for m in self.matches],
            "unmatched_bank": self.unmatched_bank,
            "unmatched_ledger": self.unmatched_ledger,
            "match_count": len(self.matches),
            "unmatched_bank_count": len(self.unmatched_bank),
            "unmatched_ledger_count": len(self.unmatched_ledger),
        }

