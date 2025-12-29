"""
Canonical transaction models matching Phase 1 schema.
"""

from dataclasses import dataclass, field
from decimal import Decimal
from datetime import datetime, date
from typing import Optional
from enum import Enum
import uuid


class TransactionSource(str, Enum):
    """Source of the transaction."""
    BANK = "bank"
    LEDGER = "ledger"


class TransactionType(str, Enum):
    """Type of transaction."""
    DEBIT = "debit"
    CREDIT = "credit"


@dataclass
class Transaction:
    """
    Canonical transaction model matching Phase 1 schema.
    
    This is the normalized representation used throughout the system.
    """
    # Core identifiers
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    source: TransactionSource = TransactionSource.BANK
    source_file: str = ""
    source_row: int = 0
    
    # Core transaction data
    date: date = None
    amount: Decimal = Decimal("0.00")
    transaction_type: TransactionType = TransactionType.DEBIT
    description: str = ""
    original_description: str = ""
    
    # Optional metadata
    reference: Optional[str] = None
    category: Optional[str] = None
    currency: str = "USD"
    
    # Reconciliation metadata (populated during matching)
    matched_with: Optional[str] = None
    match_confidence: Optional[float] = None
    match_reason: Optional[str] = None
    
    # Timestamps
    ingested_at: datetime = field(default_factory=datetime.utcnow)
    reconciled_at: Optional[datetime] = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "source": self.source.value,
            "source_file": self.source_file,
            "source_row": self.source_row,
            "date": self.date.isoformat() if self.date else None,
            "amount": str(self.amount),
            "transaction_type": self.transaction_type.value,
            "description": self.description,
            "original_description": self.original_description,
            "reference": self.reference,
            "category": self.category,
            "currency": self.currency,
            "matched_with": self.matched_with,
            "match_confidence": self.match_confidence,
            "match_reason": self.match_reason,
            "ingested_at": self.ingested_at.isoformat() if self.ingested_at else None,
            "reconciled_at": self.reconciled_at.isoformat() if self.reconciled_at else None,
        }

