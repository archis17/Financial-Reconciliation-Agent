"""
Models for discrepancy detection.
"""

from dataclasses import dataclass
from decimal import Decimal
from datetime import date
from typing import Optional, List
from enum import Enum


class DiscrepancyType(str, Enum):
    """Type of discrepancy."""
    MISSING_IN_LEDGER = "missing_in_ledger"  # Bank transaction not in ledger
    MISSING_IN_BANK = "missing_in_bank"      # Ledger transaction not in bank
    AMOUNT_MISMATCH = "amount_mismatch"       # Matched but different amounts
    DATE_MISMATCH = "date_mismatch"          # Matched but dates differ significantly
    DUPLICATE = "duplicate"                   # Same transaction appears multiple times
    POSSIBLE_FRAUD = "possible_fraud"       # Suspicious patterns
    UNMATCHED = "unmatched"                   # Generic unmatched transaction


class DiscrepancySeverity(str, Enum):
    """Severity level of discrepancy."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class Discrepancy:
    """Represents a detected discrepancy."""
    transaction_id: str
    source: str  # "bank" | "ledger"
    discrepancy_type: DiscrepancyType
    severity: DiscrepancySeverity
    
    # Machine-readable reason
    machine_reason: str
    
    # Optional human-readable explanation (from LLM in Phase 6)
    llm_explanation: Optional[str] = None
    
    # Suggested action
    suggested_action: Optional[str] = None
    
    # Related transaction (if applicable)
    related_transaction_id: Optional[str] = None
    
    # Details
    amount: Optional[Decimal] = None
    date: Optional[date] = None
    description: Optional[str] = None
    
    # For amount/date mismatches
    expected_amount: Optional[Decimal] = None
    actual_amount: Optional[Decimal] = None
    amount_difference: Optional[Decimal] = None
    
    expected_date: Optional[date] = None
    actual_date: Optional[date] = None
    date_difference_days: Optional[int] = None
    
    # Metadata
    confidence: float = 1.0  # Confidence in discrepancy detection
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "transaction_id": self.transaction_id,
            "source": self.source,
            "discrepancy_type": self.discrepancy_type.value,
            "severity": self.severity.value,
            "machine_reason": self.machine_reason,
            "llm_explanation": self.llm_explanation,
            "suggested_action": self.suggested_action,
            "related_transaction_id": self.related_transaction_id,
            "amount": str(self.amount) if self.amount else None,
            "date": self.date.isoformat() if self.date else None,
            "description": self.description,
            "expected_amount": str(self.expected_amount) if self.expected_amount else None,
            "actual_amount": str(self.actual_amount) if self.actual_amount else None,
            "amount_difference": str(self.amount_difference) if self.amount_difference else None,
            "expected_date": self.expected_date.isoformat() if self.expected_date else None,
            "actual_date": self.actual_date.isoformat() if self.actual_date else None,
            "date_difference_days": self.date_difference_days,
            "confidence": self.confidence,
        }


@dataclass
class DiscrepancyResult:
    """Result of discrepancy detection."""
    discrepancies: List[Discrepancy]
    
    # Summary counts by type
    missing_in_ledger_count: int = 0
    missing_in_bank_count: int = 0
    amount_mismatch_count: int = 0
    date_mismatch_count: int = 0
    duplicate_count: int = 0
    possible_fraud_count: int = 0
    
    # Summary counts by severity
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "total_discrepancies": len(self.discrepancies),
            "by_type": {
                "missing_in_ledger": self.missing_in_ledger_count,
                "missing_in_bank": self.missing_in_bank_count,
                "amount_mismatch": self.amount_mismatch_count,
                "date_mismatch": self.date_mismatch_count,
                "duplicate": self.duplicate_count,
                "possible_fraud": self.possible_fraud_count,
            },
            "by_severity": {
                "critical": self.critical_count,
                "high": self.high_count,
                "medium": self.medium_count,
                "low": self.low_count,
            },
            "discrepancies": [d.to_dict() for d in self.discrepancies],
        }

