"""
Discrepancy classification logic.
"""

from decimal import Decimal
from datetime import date, timedelta
from typing import Optional

from discrepancy.models import DiscrepancyType, DiscrepancySeverity
from ingestion.models import Transaction
from matching.models import Match


class DiscrepancyClassifier:
    """Classifies discrepancies and assigns severity."""
    
    def __init__(
        self,
        amount_tolerance: Decimal = Decimal("5.00"),
        date_window_days: int = 7,
        large_amount_threshold: Decimal = Decimal("10000.00")
    ):
        """
        Initialize classifier.
        
        Args:
            amount_tolerance: Normal amount tolerance
            date_window_days: Normal date window
            large_amount_threshold: Threshold for large amounts (affects severity)
        """
        self.amount_tolerance = amount_tolerance
        self.date_window_days = date_window_days
        self.large_amount_threshold = large_amount_threshold
    
    def classify_missing(
        self,
        transaction: Transaction
    ) -> tuple[DiscrepancyType, DiscrepancySeverity, str]:
        """
        Classify a missing transaction.
        
        Returns:
            Tuple of (type, severity, reason)
        """
        if transaction.source.value == "bank":
            disc_type = DiscrepancyType.MISSING_IN_LEDGER
            reason = f"Bank transaction not found in ledger: {transaction.description}"
        else:
            disc_type = DiscrepancyType.MISSING_IN_BANK
            reason = f"Ledger transaction not found in bank statement: {transaction.description}"
        
        # Severity based on amount
        if transaction.amount >= self.large_amount_threshold:
            severity = DiscrepancySeverity.CRITICAL
        elif transaction.amount >= self.large_amount_threshold / 10:
            severity = DiscrepancySeverity.HIGH
        else:
            severity = DiscrepancySeverity.MEDIUM
        
        return disc_type, severity, reason
    
    def classify_amount_mismatch(
        self,
        match: Match,
        bank_tx: Transaction,
        ledger_tx: Transaction
    ) -> tuple[DiscrepancySeverity, str]:
        """
        Classify an amount mismatch.
        
        Returns:
            Tuple of (severity, reason)
        """
        amount_diff = abs(match.amount_difference)
        percent_diff = float(amount_diff) / float(bank_tx.amount) if bank_tx.amount > 0 else 0.0
        
        # Determine severity
        if amount_diff >= self.large_amount_threshold or percent_diff > 0.1:  # >10%
            severity = DiscrepancySeverity.CRITICAL
        elif amount_diff >= self.amount_tolerance * 2 or percent_diff > 0.05:  # >5%
            severity = DiscrepancySeverity.HIGH
        elif amount_diff > self.amount_tolerance:
            severity = DiscrepancySeverity.MEDIUM
        else:
            severity = DiscrepancySeverity.LOW
        
        reason = (
            f"Amount mismatch: Bank shows ${bank_tx.amount:.2f}, "
            f"Ledger shows ${ledger_tx.amount:.2f} "
            f"(difference: ${amount_diff:.2f}, {percent_diff:.1%})"
        )
        
        return severity, reason
    
    def classify_date_mismatch(
        self,
        match: Match,
        bank_tx: Transaction,
        ledger_tx: Transaction
    ) -> tuple[DiscrepancySeverity, str]:
        """
        Classify a date mismatch.
        
        Returns:
            Tuple of (severity, reason)
        """
        date_diff = abs(match.date_difference_days)
        
        # Determine severity
        if date_diff > 30:  # More than a month
            severity = DiscrepancySeverity.HIGH
        elif date_diff > 14:  # More than 2 weeks
            severity = DiscrepancySeverity.MEDIUM
        else:
            severity = DiscrepancySeverity.LOW
        
        reason = (
            f"Date mismatch: Bank date {bank_tx.date}, "
            f"Ledger date {ledger_tx.date} "
            f"(difference: {date_diff} days)"
        )
        
        return severity, reason
    
    def classify_duplicate(
        self,
        transactions: list[Transaction]
    ) -> tuple[DiscrepancySeverity, str]:
        """
        Classify duplicate transactions.
        
        Returns:
            Tuple of (severity, reason)
        """
        # Severity based on amount
        total_amount = sum(tx.amount for tx in transactions)
        
        if total_amount >= self.large_amount_threshold:
            severity = DiscrepancySeverity.HIGH
        elif total_amount >= self.large_amount_threshold / 10:
            severity = DiscrepancySeverity.MEDIUM
        else:
            severity = DiscrepancySeverity.LOW
        
        count = len(transactions)
        reason = (
            f"Duplicate transaction detected: {count} occurrences "
            f"of same transaction (total: ${total_amount:.2f})"
        )
        
        return severity, reason
    
    def classify_suspicious(
        self,
        transaction: Transaction
    ) -> tuple[DiscrepancySeverity, str]:
        """
        Classify suspicious/fraud indicators.
        
        Returns:
            Tuple of (severity, reason)
        """
        # Simple heuristics for suspicious patterns
        suspicious_indicators = []
        
        # Very large amount
        if transaction.amount >= self.large_amount_threshold * 10:
            suspicious_indicators.append("very large amount")
        
        # Round numbers (potential test transactions)
        if transaction.amount % 1000 == 0 and transaction.amount >= 10000:
            suspicious_indicators.append("suspicious round number")
        
        # Future dates
        if transaction.date > date.today():
            suspicious_indicators.append("future date")
        
        if suspicious_indicators:
            severity = DiscrepancySeverity.CRITICAL if transaction.amount >= self.large_amount_threshold else DiscrepancySeverity.HIGH
            reason = f"Suspicious pattern detected: {', '.join(suspicious_indicators)}"
            return severity, reason
        
        return None, None

