"""
Ground truth management for synthetic data generation.
"""

from dataclasses import dataclass, asdict
from decimal import Decimal
from datetime import date
from typing import List, Dict, Optional
import json
import uuid


@dataclass
class GroundTruthEntry:
    """Represents a ground truth transaction with its representations."""
    transaction_id: str
    true_date: date
    true_amount: Decimal
    transaction_type: str  # "debit" | "credit"
    true_description: str
    
    # Bank statement representation
    bank_date: Optional[date] = None
    bank_amount: Optional[Decimal] = None
    bank_description: Optional[str] = None
    bank_present: bool = True
    
    # Ledger representation
    ledger_date: Optional[date] = None
    ledger_amount: Optional[Decimal] = None
    ledger_description: Optional[str] = None
    ledger_present: bool = True
    
    # Noise metadata
    noise_applied: Dict = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        # Convert dates to strings
        for key in ['true_date', 'bank_date', 'ledger_date']:
            if data.get(key):
                data[key] = data[key].isoformat() if isinstance(data[key], date) else data[key]
        # Convert Decimal to string
        for key in ['true_amount', 'bank_amount', 'ledger_amount']:
            if data.get(key):
                data[key] = str(data[key]) if isinstance(data[key], Decimal) else data[key]
        return data


class GroundTruthManager:
    """Manages ground truth data for validation."""
    
    def __init__(self):
        self.entries: List[GroundTruthEntry] = []
    
    def add_entry(self, entry: GroundTruthEntry):
        """Add a ground truth entry."""
        self.entries.append(entry)
    
    def get_matches(self) -> List[Dict]:
        """
        Get all matching pairs (bank -> ledger).
        
        Returns:
            List of match dictionaries with transaction IDs
        """
        matches = []
        for entry in self.entries:
            if entry.bank_present and entry.ledger_present:
                matches.append({
                    "bank_transaction_id": f"bank_{entry.transaction_id}",
                    "ledger_transaction_id": f"ledger_{entry.transaction_id}",
                    "true_transaction_id": entry.transaction_id,
                    "confidence_expected": self._calculate_expected_confidence(entry)
                })
        return matches
    
    def get_missing_in_bank(self) -> List[str]:
        """Get transaction IDs missing in bank statement."""
        return [
            f"ledger_{entry.transaction_id}"
            for entry in self.entries
            if not entry.bank_present and entry.ledger_present
        ]
    
    def get_missing_in_ledger(self) -> List[str]:
        """Get transaction IDs missing in ledger."""
        return [
            f"bank_{entry.transaction_id}"
            for entry in self.entries
            if entry.bank_present and not entry.ledger_present
        ]
    
    def _calculate_expected_confidence(self, entry: GroundTruthEntry) -> float:
        """
        Calculate expected confidence score based on noise applied.
        
        Returns:
            Expected confidence (0.0 to 1.0)
        """
        if not entry.noise_applied:
            return 1.0
        
        confidence = 1.0
        
        # Reduce confidence for date drift
        if entry.noise_applied.get("date_drift_days", 0) != 0:
            drift_days = abs(entry.noise_applied["date_drift_days"])
            confidence -= min(0.3, drift_days * 0.05)
        
        # Reduce confidence for amount difference
        if abs(entry.noise_applied.get("amount_difference", 0)) > 0:
            confidence -= 0.2
        
        # Reduce confidence for description variation
        if entry.noise_applied.get("description_variation") == "major":
            confidence -= 0.3
        elif entry.noise_applied.get("description_variation") == "minor":
            confidence -= 0.1
        
        return max(0.0, min(1.0, confidence))
    
    def get_statistics(self) -> Dict:
        """Get statistics about the ground truth data."""
        total = len(self.entries)
        matches = sum(1 for e in self.entries if e.bank_present and e.ledger_present)
        missing_bank = sum(1 for e in self.entries if not e.bank_present and e.ledger_present)
        missing_ledger = sum(1 for e in self.entries if e.bank_present and not e.ledger_present)
        
        return {
            "total_transactions": total,
            "matched_transactions": matches,
            "missing_in_bank": missing_bank,
            "missing_in_ledger": missing_ledger,
            "match_rate": matches / total if total > 0 else 0.0,
            "noise_statistics": self._get_noise_statistics()
        }
    
    def _get_noise_statistics(self) -> Dict:
        """Get statistics about noise applied."""
        date_drifts = []
        amount_differences = []
        description_variations = {"none": 0, "minor": 0, "major": 0}
        
        for entry in self.entries:
            if entry.noise_applied:
                if "date_drift_days" in entry.noise_applied:
                    date_drifts.append(abs(entry.noise_applied["date_drift_days"]))
                if "amount_difference" in entry.noise_applied:
                    amount_differences.append(abs(entry.noise_applied["amount_difference"]))
                if "description_variation" in entry.noise_applied:
                    desc_var = entry.noise_applied["description_variation"]
                    description_variations[desc_var] = description_variations.get(desc_var, 0) + 1
        
        return {
            "avg_date_drift_days": sum(date_drifts) / len(date_drifts) if date_drifts else 0,
            "max_date_drift_days": max(date_drifts) if date_drifts else 0,
            "avg_amount_difference": sum(amount_differences) / len(amount_differences) if amount_differences else 0,
            "max_amount_difference": max(amount_differences) if amount_differences else 0,
            "description_variations": description_variations
        }
    
    def save(self, filepath: str):
        """Save ground truth to JSON file."""
        data = {
            "entries": [entry.to_dict() for entry in self.entries],
            "statistics": self.get_statistics(),
            "matches": self.get_matches(),
            "missing_in_bank": self.get_missing_in_bank(),
            "missing_in_ledger": self.get_missing_in_ledger()
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2, default=str)
    
    @classmethod
    def load(cls, filepath: str) -> 'GroundTruthManager':
        """Load ground truth from JSON file."""
        manager = cls()
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        # Reconstruct entries (simplified - would need proper date/Decimal parsing)
        # This is mainly for reference, full reconstruction would need more work
        return manager

