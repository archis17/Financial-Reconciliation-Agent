"""
Confidence scoring for matches.
"""

from dataclasses import dataclass
from typing import Optional
from decimal import Decimal

from .models import MatchType
from .rules import RuleBasedMatcher


@dataclass
class ScoringWeights:
    """Weights for different match signals."""
    amount_weight: float = 0.30
    date_weight: float = 0.20
    description_weight: float = 0.50  # Sums to 1.0 with amount and date
    reference_weight: float = 0.10  # Bonus weight (not included in base sum)
    
    def validate(self):
        """Validate that weights sum to approximately 1.0."""
        total = self.amount_weight + self.date_weight + self.description_weight
        if abs(total - 1.0) > 0.01:
            raise ValueError(f"Weights must sum to 1.0, got {total}")


class ConfidenceScorer:
    """Calculates confidence scores for matches."""
    
    def __init__(
        self,
        weights: Optional[ScoringWeights] = None,
        reference_bonus: float = 0.1
    ):
        """
        Initialize confidence scorer.
        
        Args:
            weights: Scoring weights (default: standard weights)
            reference_bonus: Bonus confidence for reference match
        """
        self.weights = weights or ScoringWeights()
        self.weights.validate()
        self.reference_bonus = reference_bonus
    
    def calculate_confidence(
        self,
        amount_score: float,
        date_score: float,
        description_score: float,
        reference_match: bool = False
    ) -> float:
        """
        Calculate overall confidence score.
        
        Args:
            amount_score: Amount matching score (0.0 to 1.0)
            date_score: Date matching score (0.0 to 1.0)
            description_score: Description similarity score (0.0 to 1.0)
            reference_match: Whether references match
        
        Returns:
            Overall confidence score (0.0 to 1.0)
        """
        # Weighted combination
        base_confidence = (
            self.weights.amount_weight * amount_score +
            self.weights.date_weight * date_score +
            self.weights.description_weight * description_score
        )
        
        # Add reference bonus
        if reference_match:
            base_confidence += self.reference_bonus
        
        # Clamp to [0.0, 1.0] and convert to Python float (not numpy float32)
        return float(max(0.0, min(1.0, base_confidence)))
    
    def determine_match_type(
        self,
        amount_score: float,
        date_score: float,
        description_score: float,
        reference_match: bool,
        confidence: float
    ) -> MatchType:
        """
        Determine the type of match based on scores.
        
        Returns:
            MatchType enum value
        """
        # Exact match: all scores are 1.0
        if amount_score == 1.0 and date_score == 1.0 and description_score >= 0.9:
            return MatchType.EXACT
        
        # Fuzzy match: rule-based (amount and date within tolerance)
        if amount_score > 0.0 and date_score > 0.0 and description_score < 0.7:
            return MatchType.FUZZY
        
        # Semantic match: high description similarity but amount/date issues
        if description_score >= 0.7 and (amount_score < 0.5 or date_score < 0.5):
            return MatchType.SEMANTIC
        
        # Combined: mix of signals
        return MatchType.COMBINED

