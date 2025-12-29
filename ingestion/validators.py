"""
Validation utilities for transactions.
"""

from decimal import Decimal
from datetime import date, datetime
from typing import List, Dict, Optional
import logging

from .models import Transaction

logger = logging.getLogger(__name__)


class ValidationError:
    """Represents a validation error."""
    
    def __init__(self, field: str, message: str, severity: str = "error"):
        self.field = field
        self.message = message
        self.severity = severity  # "error" | "warning"
    
    def to_dict(self) -> dict:
        return {
            "field": self.field,
            "message": self.message,
            "severity": self.severity
        }


class TransactionValidator:
    """Validates transaction data."""
    
    def __init__(self, strict: bool = False):
        """
        Initialize validator.
        
        Args:
            strict: If True, treat warnings as errors
        """
        self.strict = strict
    
    def validate(self, transaction: Transaction) -> List[ValidationError]:
        """
        Validate a transaction.
        
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        # Required fields
        if not transaction.date:
            errors.append(ValidationError("date", "Date is required", "error"))
        
        if transaction.amount is None or transaction.amount == Decimal("0.00"):
            errors.append(ValidationError("amount", "Amount must be greater than zero", "error"))
        
        if not transaction.description:
            errors.append(ValidationError("description", "Description is required", "warning"))
        
        # Date validation
        if transaction.date:
            # Check if date is reasonable (not too far in past/future)
            today = date.today()
            years_ago = (today - transaction.date).days / 365.25
            
            if years_ago > 10:
                errors.append(ValidationError(
                    "date",
                    f"Date is more than 10 years in the past: {transaction.date}",
                    "warning"
                ))
            elif transaction.date > today:
                # Future dates might be pending transactions
                days_ahead = (transaction.date - today).days
                if days_ahead > 90:
                    errors.append(ValidationError(
                        "date",
                        f"Date is more than 90 days in the future: {transaction.date}",
                        "warning"
                    ))
        
        # Amount validation
        if transaction.amount:
            if transaction.amount < Decimal("0.00"):
                errors.append(ValidationError(
                    "amount",
                    f"Amount is negative: {transaction.amount}",
                    "error"
                ))
            
            # Warn about very large amounts
            if transaction.amount > Decimal("1000000.00"):
                errors.append(ValidationError(
                    "amount",
                    f"Amount is very large: {transaction.amount}",
                    "warning"
                ))
        
        # Description validation
        if transaction.description:
            if len(transaction.description) > 500:
                errors.append(ValidationError(
                    "description",
                    "Description is very long (over 500 characters)",
                    "warning"
                ))
        
        # Currency validation
        if transaction.currency and len(transaction.currency) != 3:
            errors.append(ValidationError(
                "currency",
                f"Currency code should be 3 characters (ISO 4217): {transaction.currency}",
                "warning"
            ))
        
        return errors
    
    def validate_batch(self, transactions: List[Transaction]) -> Dict[str, List[ValidationError]]:
        """
        Validate a batch of transactions.
        
        Returns:
            Dictionary mapping transaction ID to list of errors
        """
        results = {}
        
        for tx in transactions:
            errors = self.validate(tx)
            if errors:
                results[tx.id] = errors
        
        return results

