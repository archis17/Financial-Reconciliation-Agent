"""
Noise injection logic for realistic data generation.
"""

from dataclasses import dataclass
from decimal import Decimal
from datetime import date, timedelta
from typing import Optional
import random


@dataclass
class NoiseConfig:
    """Configuration for noise injection."""
    date_drift_max_days: int = 7
    amount_tolerance_max: Decimal = Decimal("5.00")
    description_variation_rate: float = 0.3  # 30% chance of variation
    missing_rate: float = 0.05  # 5% chance of missing entry


@dataclass
class NoiseResult:
    """Result of noise injection."""
    date: date
    amount: Decimal
    description: str
    present: bool  # False if this entry should be missing
    noise_applied: dict


class NoiseInjector:
    """Injects realistic noise into transaction data."""
    
    def __init__(self, config: NoiseConfig):
        self.config = config
    
    def inject_noise(
        self,
        true_date: date,
        true_amount: Decimal,
        true_description: str,
        variation_level: str = "none"
    ) -> NoiseResult:
        """
        Inject noise into a transaction.
        
        Args:
            true_date: Original transaction date
            true_amount: Original transaction amount
            true_description: Original description
            variation_level: "none", "minor", or "major" for description variation
        
        Returns:
            NoiseResult with potentially modified values
        """
        # Check if entry should be missing
        if random.random() < self.config.missing_rate:
            return NoiseResult(
                date=true_date,
                amount=true_amount,
                description=true_description,
                present=False,
                noise_applied={"missing": True}
            )
        
        # Inject date drift
        date_drift = 0
        if random.random() < 0.4:  # 40% chance of date drift
            date_drift = random.randint(-self.config.date_drift_max_days, self.config.date_drift_max_days)
        
        noisy_date = true_date + timedelta(days=date_drift)
        
        # Inject amount difference
        amount_difference = Decimal("0.00")
        if random.random() < 0.2:  # 20% chance of amount mismatch
            # Amount difference can be positive or negative (e.g., fees, rounding)
            max_diff = min(self.config.amount_tolerance_max, true_amount * Decimal("0.05"))
            amount_difference = Decimal(str(random.uniform(-float(max_diff), float(max_diff))))
            amount_difference = amount_difference.quantize(Decimal("0.01"))
        
        noisy_amount = true_amount + amount_difference
        
        # Inject description variation
        noisy_description = true_description
        description_variation = "none"
        if random.random() < self.config.description_variation_rate:
            if variation_level == "major":
                noisy_description = self._vary_description_major(true_description)
                description_variation = "major"
            elif variation_level == "minor":
                noisy_description = self._vary_description_minor(true_description)
                description_variation = "minor"
        
        return NoiseResult(
            date=noisy_date,
            amount=noisy_amount,
            description=noisy_description,
            present=True,
            noise_applied={
                "date_drift_days": date_drift,
                "amount_difference": float(amount_difference),
                "description_variation": description_variation
            }
        )
    
    def _vary_description_minor(self, description: str) -> str:
        """Apply minor variations to description."""
        variations = [
            lambda s: s.upper(),
            lambda s: s.lower(),
            lambda s: s.title(),
            lambda s: s.replace("  ", " "),
            lambda s: s.replace("#", "No."),
            lambda s: s.replace("&", "AND"),
        ]
        variation = random.choice(variations)
        return variation(description)
    
    def _vary_description_major(self, description: str) -> str:
        """Apply major variations to description."""
        # More significant changes
        variations = [
            lambda s: s.replace("AMAZON.COM", "Amazon Marketplace"),
            lambda s: s.replace("STARBUCKS", "Coffee Shop Purchase"),
            lambda s: s.replace("PAYROLL", "Salary Deposit"),
            lambda s: s.replace("OFFICE DEPOT", "Office Supplies Store"),
            lambda s: s.replace("BANK FEE", "Service Charge"),
            lambda s: s.replace("TRANSFER", "Bank Transfer"),
            lambda s: s.replace("VENDOR", "Supplier Payment"),
            lambda s: s.replace("NETFLIX", "Streaming Service"),
            lambda s: s.replace("FUEL", "Gas Station"),
            lambda s: s.replace("GAS STATION", "Fuel Purchase"),
        ]
        
        # Try to find a matching variation
        for variation in variations:
            if variation(description) != description:
                return variation(description)
        
        # Fallback to minor variation
        return self._vary_description_minor(description)

