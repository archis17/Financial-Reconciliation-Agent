"""
Models for reporting and ticket generation.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Dict
from decimal import Decimal


@dataclass
class ReconciliationReport:
    """Reconciliation report data structure."""
    reconciliation_id: str
    run_at: datetime
    status: str  # "completed" | "partial" | "failed"
    
    # Summary
    bank_transactions_count: int
    ledger_transactions_count: int
    matched_count: int
    unmatched_bank_count: int
    unmatched_ledger_count: int
    discrepancy_count: int
    
    # Performance metrics
    processing_time_seconds: float
    llm_calls_made: int = 0
    llm_tokens_used: int = 0
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "reconciliation_id": self.reconciliation_id,
            "run_at": self.run_at.isoformat(),
            "status": self.status,
            "bank_transactions_count": self.bank_transactions_count,
            "ledger_transactions_count": self.ledger_transactions_count,
            "matched_count": self.matched_count,
            "unmatched_bank_count": self.unmatched_bank_count,
            "unmatched_ledger_count": self.unmatched_ledger_count,
            "discrepancy_count": self.discrepancy_count,
            "processing_time_seconds": self.processing_time_seconds,
            "llm_calls_made": self.llm_calls_made,
            "llm_tokens_used": self.llm_tokens_used,
        }


@dataclass
class Ticket:
    """Accounting ticket for issue tracking systems."""
    ticket_type: str  # "discrepancy" | "review_required" | "action_item"
    title: str
    description: str
    priority: str  # "low" | "medium" | "high" | "critical"
    severity: str  # "low" | "medium" | "high" | "critical"
    
    # Transaction details
    transaction_id: Optional[str] = None
    amount: Optional[Decimal] = None
    date: Optional[datetime] = None
    transaction_description: Optional[str] = None
    
    # Discrepancy details
    discrepancy_type: Optional[str] = None
    machine_reason: Optional[str] = None
    llm_explanation: Optional[str] = None
    suggested_action: Optional[str] = None
    
    # Metadata
    labels: List[str] = None
    assignee: Optional[str] = None
    due_date: Optional[datetime] = None
    custom_fields: Dict[str, str] = None
    
    def __post_init__(self):
        """Initialize default values."""
        if self.labels is None:
            self.labels = []
        if self.custom_fields is None:
            self.custom_fields = {}
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "ticket_type": self.ticket_type,
            "title": self.title,
            "description": self.description,
            "priority": self.priority,
            "severity": self.severity,
            "transaction_id": self.transaction_id,
            "amount": str(self.amount) if self.amount else None,
            "date": self.date.isoformat() if self.date else None,
            "transaction_description": self.transaction_description,
            "discrepancy_type": self.discrepancy_type,
            "machine_reason": self.machine_reason,
            "llm_explanation": self.llm_explanation,
            "suggested_action": self.suggested_action,
            "labels": self.labels,
            "assignee": self.assignee,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "custom_fields": self.custom_fields,
        }

