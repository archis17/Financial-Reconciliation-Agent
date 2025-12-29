"""
Models for LLM explanation service.
"""

from dataclasses import dataclass
from typing import Optional
from decimal import Decimal
from datetime import date


@dataclass
class ExplanationRequest:
    """Request for LLM explanation."""
    discrepancy_type: str
    transaction_description: str
    amount: Optional[Decimal] = None
    date: Optional[date] = None
    machine_reason: str = ""
    severity: str = ""
    amount_difference: Optional[Decimal] = None
    date_difference_days: Optional[int] = None
    related_transaction_info: Optional[str] = None


@dataclass
class ExplanationResponse:
    """Response from LLM explanation service."""
    explanation: str
    suggested_action: str
    confidence: float = 1.0
    tokens_used: int = 0
    model_used: str = ""
    error: Optional[str] = None

