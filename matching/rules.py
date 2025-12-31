"""
Rule-based matching logic.
"""

from dataclasses import dataclass
from decimal import Decimal
from datetime import date, timedelta
from typing import Optional
import logging

from ingestion.models import Transaction

logger = logging.getLogger(__name__)


@dataclass
class MatchingConfig:
    """Configuration for matching rules."""
    amount_tolerance: Decimal = Decimal("5.00")  # Max amount difference
    amount_tolerance_percent: float = 0.01  # 1% tolerance
    date_window_days: int = 7  # Max days difference
    require_same_type: bool = True  # Must be same transaction type (debit/credit)
    reference_match_bonus: float = 0.1  # Bonus confidence for reference match


class RuleBasedMatcher:
    """Rule-based matching using amount, date, and reference."""
    
    def __init__(self, config: MatchingConfig):
        self.config = config
    
    def calculate_amount_score(
        self,
        bank_amount: Decimal,
        ledger_amount: Decimal
    ) -> tuple:
        """
        Calculate amount matching score.
        
        Returns:
            Tuple of (score, difference)
            Score is 1.0 for exact match, decreasing with difference
        """
        difference = abs(bank_amount - ledger_amount)
        
        # Exact match
        if difference == Decimal("0.00"):
            return (1.0, difference)
        
        # Check absolute tolerance
        if difference <= self.config.amount_tolerance:
            # Score decreases linearly within tolerance
            score = 1.0 - (float(difference) / float(self.config.amount_tolerance))
            return (float(max(0.0, score)), difference)  # Convert to Python float
        
        # Check percentage tolerance
        avg_amount = (bank_amount + ledger_amount) / 2
        if avg_amount > Decimal("0.00"):
            percent_diff = float(difference) / float(avg_amount)
            if percent_diff <= self.config.amount_tolerance_percent:
                # Score based on percentage
                score = 1.0 - (percent_diff / self.config.amount_tolerance_percent)
                return (float(max(0.0, score)), difference)  # Convert to Python float
        
        # Outside tolerance
        return (0.0, difference)  # Already Python float
    
    def calculate_date_score(
        self,
        bank_date: date,
        ledger_date: date
    ) -> tuple:
        """
        Calculate date matching score.
        
        Returns:
            Tuple of (score, difference_days)
            Score is 1.0 for exact match, decreasing with days difference
        """
        difference_days = abs((bank_date - ledger_date).days)
        
        # Exact match
        if difference_days == 0:
            return (1.0, difference_days)  # Already Python float
        
        # Within window
        if difference_days <= self.config.date_window_days:
            # Score decreases linearly within window
            score = 1.0 - (difference_days / self.config.date_window_days)
            return (float(max(0.0, score)), difference_days)  # Convert to Python float
        
        # Outside window
        return (0.0, difference_days)  # Already Python float
    
    def calculate_reference_score(
        self,
        bank_reference: Optional[str],
        ledger_reference: Optional[str]
    ) -> bool:
        """
        Check if references match.
        
        Returns:
            True if references match (exact or partial)
        """
        if not bank_reference or not ledger_reference:
            return False
        
        # Normalize references (remove whitespace, case-insensitive)
        bank_ref = str(bank_reference).strip().upper()
        ledger_ref = str(ledger_reference).strip().upper()
        
        # Exact match
        if bank_ref == ledger_ref:
            return True
        
        # Partial match (one contains the other)
        if bank_ref in ledger_ref or ledger_ref in bank_ref:
            return True
        
        return False
    
    def can_match(
        self,
        bank_tx: Transaction,
        ledger_tx: Transaction
    ) -> bool:
        """
        Quick check if two transactions could potentially match.
        
        Returns:
            True if transactions could match based on basic rules
        """
        # Check transaction type
        if self.config.require_same_type:
            if bank_tx.transaction_type != ledger_tx.transaction_type:
                return False
        
        # Check date window
        date_diff = abs((bank_tx.date - ledger_tx.date).days)
        if date_diff > self.config.date_window_days:
            return False
        
        # Check amount tolerance (quick check)
        amount_diff = abs(bank_tx.amount - ledger_tx.amount)
        if amount_diff > self.config.amount_tolerance * 2:  # More lenient for quick check
            # Also check percentage
            avg_amount = (bank_tx.amount + ledger_tx.amount) / 2
            if avg_amount > Decimal("0.00"):
                percent_diff = float(amount_diff) / float(avg_amount)
                if percent_diff > self.config.amount_tolerance_percent * 2:
                    return False
        
        return True
    
    def match(
        self,
        bank_tx: Transaction,
        ledger_tx: Transaction
    ) -> Optional[dict]:
        """
        Attempt to match two transactions using rules.
        
        Returns:
            Dictionary with match details if match found, None otherwise
        """
        # Quick pre-check
        if not self.can_match(bank_tx, ledger_tx):
            return None
        
        # Calculate scores
        amount_score, amount_diff = self.calculate_amount_score(
            bank_tx.amount, ledger_tx.amount
        )
        date_score, date_diff = self.calculate_date_score(
            bank_tx.date, ledger_tx.date
        )
        reference_match = self.calculate_reference_score(
            bank_tx.reference, ledger_tx.reference
        )
        
        # Determine if this is a match
        # Require both amount and date to have some score
        if amount_score > 0.0 and date_score > 0.0:
            return {
                "amount_score": amount_score,
                "date_score": date_score,
                "reference_match": reference_match,
                "amount_difference": amount_diff,
                "date_difference_days": date_diff,
            }
        
        return None

