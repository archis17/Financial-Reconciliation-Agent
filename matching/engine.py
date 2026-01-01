"""
Main matching engine orchestrating all matching components.
"""

import logging
from typing import List, Set
from decimal import Decimal

from ingestion.models import Transaction
from .models import Match, MatchType, MatchResult
from .rules import RuleBasedMatcher, MatchingConfig
from .embeddings import EmbeddingMatcher
from .scorer import ConfidenceScorer, ScoringWeights

logger = logging.getLogger(__name__)


class MatchingEngine:
    """Main matching engine combining rule-based and embedding-based matching."""
    
    def __init__(
        self,
        matching_config: MatchingConfig = None,
        scoring_weights: ScoringWeights = None,
        embedding_model: str = "all-MiniLM-L6-v2"
    ):
        """
        Initialize matching engine.
        
        Args:
            matching_config: Configuration for rule-based matching
            scoring_weights: Weights for confidence scoring
            embedding_model: Name of embedding model to use
        """
        self.rule_matcher = RuleBasedMatcher(matching_config or MatchingConfig())
        self.embedding_matcher = EmbeddingMatcher(model_name=embedding_model)
        self.scorer = ConfidenceScorer(weights=scoring_weights)
        self.config = matching_config or MatchingConfig()
    
    def match(
        self,
        bank_transactions: List[Transaction],
        ledger_transactions: List[Transaction],
        min_confidence: float = 0.6
    ) -> MatchResult:
        """
        Match bank transactions with ledger transactions.
        
        Args:
            bank_transactions: List of bank transactions
            ledger_transactions: List of ledger transactions
            min_confidence: Minimum confidence threshold for matches
        
        Returns:
            MatchResult with matches and unmatched transactions
        """
        logger.info(
            f"Matching {len(bank_transactions)} bank transactions "
            f"with {len(ledger_transactions)} ledger transactions"
        )
        
        matches: List[Match] = []
        matched_bank_ids: Set[str] = set()
        matched_ledger_ids: Set[str] = set()
        
        # Pre-filter ledger transactions by date window for efficiency
        # (This is a simple optimization - could be enhanced)
        
        # Match each bank transaction
        for bank_tx in bank_transactions:
            if bank_tx.id in matched_bank_ids:
                continue
            
            best_match = None
            best_confidence = 0.0
            
            # Try to find matching ledger transaction
            for ledger_tx in ledger_transactions:
                if ledger_tx.id in matched_ledger_ids:
                    continue
                
                # Rule-based matching
                rule_match = self.rule_matcher.match(bank_tx, ledger_tx)
                
                if rule_match:
                    # Get description similarity
                    description_sim = self.embedding_matcher.calculate_similarity(
                        bank_tx.description,
                        ledger_tx.description
                    )
                    
                    # Calculate confidence
                    confidence = self.scorer.calculate_confidence(
                        amount_score=rule_match["amount_score"],
                        date_score=rule_match["date_score"],
                        description_score=description_sim,
                        reference_match=rule_match["reference_match"]
                    )
                    
                    # Determine match type
                    match_type = self.scorer.determine_match_type(
                        amount_score=rule_match["amount_score"],
                        date_score=rule_match["date_score"],
                        description_score=description_sim,
                        reference_match=rule_match["reference_match"],
                        confidence=confidence
                    )
                    
                    # Check if this is better than current best
                    if confidence > best_confidence and confidence >= min_confidence:
                        best_confidence = confidence
                        best_match = {
                            "ledger_tx": ledger_tx,
                            "confidence": confidence,
                            "match_type": match_type,
                            "amount_score": rule_match["amount_score"],
                            "date_score": rule_match["date_score"],
                            "description_score": description_sim,
                            "reference_match": rule_match["reference_match"],
                            "amount_difference": rule_match["amount_difference"],
                            "date_difference_days": rule_match["date_difference_days"],
                        }
            
            # Create match if found
            if best_match:
                match = Match(
                    bank_transaction_id=bank_tx.id,
                    ledger_transaction_id=best_match["ledger_tx"].id,
                    confidence=float(best_match["confidence"]),  # Ensure Python float
                    match_type=best_match["match_type"],
                    amount_difference=best_match["amount_difference"],
                    date_difference_days=best_match["date_difference_days"],
                    description_similarity=float(best_match["description_score"]),  # Ensure Python float
                    reference_match=best_match["reference_match"],
                    amount_score=float(best_match["amount_score"]),  # Ensure Python float
                    date_score=float(best_match["date_score"]),  # Ensure Python float
                    description_score=float(best_match["description_score"]),  # Ensure Python float
                    reference_score=1.0 if best_match["reference_match"] else 0.0,  # Already Python float
                )
                
                matches.append(match)
                matched_bank_ids.add(bank_tx.id)
                matched_ledger_ids.add(best_match["ledger_tx"].id)
        
        # Find unmatched transactions
        unmatched_bank = [
            tx.id for tx in bank_transactions
            if tx.id not in matched_bank_ids
        ]
        unmatched_ledger = [
            tx.id for tx in ledger_transactions
            if tx.id not in matched_ledger_ids
        ]
        
        logger.info(
            f"Matched {len(matches)} transactions "
            f"({len(unmatched_bank)} unmatched bank, {len(unmatched_ledger)} unmatched ledger)"
        )
        
        return MatchResult(
            matches=matches,
            unmatched_bank=unmatched_bank,
            unmatched_ledger=unmatched_ledger
        )

