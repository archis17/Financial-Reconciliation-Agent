"""
Data normalization utilities.
"""

from decimal import Decimal, InvalidOperation
from datetime import datetime, date
from typing import Optional, Tuple
import re
import logging

logger = logging.getLogger(__name__)


class DateNormalizer:
    """Normalizes dates from various formats."""
    
    # Common date formats
    DATE_FORMATS = [
        "%Y-%m-%d",      # ISO format
        "%m/%d/%Y",      # US format
        "%d/%m/%Y",      # European format
        "%Y/%m/%d",      # Alternative ISO
        "%m-%d-%Y",      # US with dashes
        "%d-%m-%Y",      # European with dashes
        "%Y%m%d",        # Compact format
        "%B %d, %Y",     # "January 15, 2024"
        "%b %d, %Y",     # "Jan 15, 2024"
        "%d %B %Y",      # "15 January 2024"
    ]
    
    @classmethod
    def normalize(cls, date_str: str) -> Optional[date]:
        """
        Normalize a date string to a date object.
        
        Args:
            date_str: Date string in various formats
        
        Returns:
            Normalized date object, or None if parsing fails
        """
        if not date_str or not isinstance(date_str, str):
            return None
        
        # Clean the string
        date_str = date_str.strip()
        
        # Try parsing with each format
        for fmt in cls.DATE_FORMATS:
            try:
                dt = datetime.strptime(date_str, fmt)
                return dt.date()
            except (ValueError, TypeError):
                continue
        
        # Try pandas-style parsing as fallback
        try:
            from dateutil import parser
            dt = parser.parse(date_str)
            return dt.date()
        except (ValueError, TypeError, ImportError):
            pass
        
        logger.warning(f"Could not parse date: {date_str}")
        return None


class AmountNormalizer:
    """Normalizes amounts and determines transaction type."""
    
    @classmethod
    def normalize(
        cls,
        amount_str: str,
        debit_amount: Optional[str] = None,
        credit_amount: Optional[str] = None,
        transaction_type_str: Optional[str] = None
    ) -> Tuple[Decimal, str]:
        """
        Normalize amount and determine transaction type.
        
        Args:
            amount_str: Main amount field (may be positive or negative)
            debit_amount: Separate debit field (if exists)
            credit_amount: Separate credit field (if exists)
            transaction_type_str: Explicit transaction type (if provided)
        
        Returns:
            Tuple of (normalized_amount, transaction_type)
            Amount is always positive, type is "debit" or "credit"
        """
        # If explicit type provided, use it
        if transaction_type_str:
            type_lower = transaction_type_str.lower().strip()
            if type_lower in ["debit", "dr", "withdrawal", "payment", "expense"]:
                tx_type = "debit"
            elif type_lower in ["credit", "cr", "deposit", "income", "receipt"]:
                tx_type = "credit"
            else:
                tx_type = "debit"  # Default
        else:
            tx_type = None
        
        # Parse amounts
        main_amount = cls._parse_amount(amount_str) if amount_str else Decimal("0.00")
        debit_amt = cls._parse_amount(debit_amount) if debit_amount else Decimal("0.00")
        credit_amt = cls._parse_amount(credit_amount) if credit_amount else Decimal("0.00")
        
        # Determine amount and type from separate debit/credit columns
        if debit_amt > 0 or credit_amt > 0:
            if debit_amt > 0:
                return (debit_amt, "debit")
            else:
                return (credit_amt, "credit")
        
        # Determine from main amount (negative = debit, positive = credit)
        # OR positive amount with type determined by sign
        if main_amount < 0:
            return (abs(main_amount), "debit")
        elif main_amount > 0:
            # Positive amount: need to infer type
            # Common convention: positive in debit column = debit, positive in credit column = credit
            # If we have explicit type, use it
            if tx_type:
                return (main_amount, tx_type)
            # Default: positive amounts are credits (deposits)
            return (main_amount, "credit")
        else:
            # Zero amount - default to debit
            return (Decimal("0.00"), "debit")
    
    @classmethod
    def _parse_amount(cls, amount_str: str) -> Decimal:
        """Parse amount string to Decimal."""
        if not amount_str:
            return Decimal("0.00")
        
        # Convert to string and clean
        amount_str = str(amount_str).strip()
        
        # Remove currency symbols and commas
        amount_str = re.sub(r'[$,\s]', '', amount_str)
        
        # Handle parentheses (accounting notation for negatives)
        if amount_str.startswith('(') and amount_str.endswith(')'):
            amount_str = '-' + amount_str[1:-1]
        
        try:
            return Decimal(amount_str).quantize(Decimal("0.01"))
        except (InvalidOperation, ValueError) as e:
            logger.warning(f"Could not parse amount: {amount_str}, error: {e}")
            return Decimal("0.00")


class DescriptionNormalizer:
    """Normalizes transaction descriptions."""
    
    @classmethod
    def normalize(cls, description: str, preserve_original: bool = True) -> Tuple[str, str]:
        """
        Normalize description text.
        
        Args:
            description: Raw description string
            preserve_original: Whether to return original separately
        
        Returns:
            Tuple of (normalized_description, original_description)
        """
        if not description:
            return ("", "")
        
        original = str(description).strip()
        
        # Normalize: remove extra whitespace, but preserve structure
        normalized = re.sub(r'\s+', ' ', original)
        normalized = normalized.strip()
        
        # Optionally normalize case (but preserve for now - matching will handle case-insensitivity)
        # normalized = normalized.upper()  # Uncomment if needed
        
        if preserve_original:
            return (normalized, original)
        else:
            return (normalized, normalized)
    
    @classmethod
    def clean_for_matching(cls, description: str) -> str:
        """
        Clean description for matching purposes.
        
        More aggressive cleaning for similarity matching.
        """
        if not description:
            return ""
        
        # Remove special characters, normalize whitespace
        cleaned = re.sub(r'[^\w\s]', ' ', description)
        cleaned = re.sub(r'\s+', ' ', cleaned)
        cleaned = cleaned.strip().upper()
        
        return cleaned

