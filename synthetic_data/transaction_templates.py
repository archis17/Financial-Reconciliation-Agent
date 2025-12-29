"""
Realistic transaction templates for synthetic data generation.
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import List, Dict, Tuple
import random
from datetime import date, timedelta


@dataclass
class TransactionTemplate:
    """Template for generating realistic transactions."""
    description_patterns: List[str]
    amount_range: Tuple[Decimal, Decimal]
    frequency: str  # "daily", "weekly", "monthly", "one_time"
    transaction_type: str  # "debit" | "credit"
    category: str
    description_variations: List[str] = None


# Common merchant patterns
MERCHANT_TEMPLATES: List[TransactionTemplate] = [
    TransactionTemplate(
        description_patterns=["AMAZON.COM", "Amazon", "AMZN"],
        amount_range=(Decimal("10.00"), Decimal("500.00")),
        frequency="daily",
        transaction_type="debit",
        category="Retail",
        description_variations=[
            "AMAZON.COM PURCHASE",
            "Amazon Prime Subscription",
            "Amazon Marketplace",
            "AMZN Mktp US",
            "Amazon.com*Purchase"
        ]
    ),
    TransactionTemplate(
        description_patterns=["STARBUCKS", "Starbucks"],
        amount_range=(Decimal("3.50"), Decimal("15.00")),
        frequency="daily",
        transaction_type="debit",
        category="Food & Beverage",
        description_variations=[
            "STARBUCKS #1234",
            "Starbucks Store 1234",
            "STARBUCKS COFFEE",
            "Starbucks Card Reload"
        ]
    ),
    TransactionTemplate(
        description_patterns=["PAYROLL", "SALARY", "WAGES"],
        amount_range=(Decimal("2000.00"), Decimal("10000.00")),
        frequency="monthly",
        transaction_type="credit",
        category="Income",
        description_variations=[
            "PAYROLL DEPOSIT",
            "Direct Deposit - Payroll",
            "SALARY PAYMENT",
            "Employee Payroll",
            "WAGES DEPOSIT"
        ]
    ),
    TransactionTemplate(
        description_patterns=["OFFICE DEPOT", "Office Depot"],
        amount_range=(Decimal("20.00"), Decimal("300.00")),
        frequency="weekly",
        transaction_type="debit",
        category="Office Supplies",
        description_variations=[
            "OFFICE DEPOT #5678",
            "Office Depot Store",
            "OFFICE DEPOT ONLINE",
            "Office Supplies - Office Depot"
        ]
    ),
    TransactionTemplate(
        description_patterns=["UTILITY", "ELECTRIC", "GAS"],
        amount_range=(Decimal("50.00"), Decimal("500.00")),
        frequency="monthly",
        transaction_type="debit",
        category="Utilities",
        description_variations=[
            "ELECTRIC BILL PAYMENT",
            "Utility Payment - Electric",
            "GAS COMPANY BILL",
            "Monthly Utility Charge"
        ]
    ),
    TransactionTemplate(
        description_patterns=["BANK FEE", "SERVICE CHARGE"],
        amount_range=(Decimal("5.00"), Decimal("50.00")),
        frequency="monthly",
        transaction_type="debit",
        category="Bank Fees",
        description_variations=[
            "MONTHLY SERVICE FEE",
            "Bank Service Charge",
            "ACCOUNT MAINTENANCE FEE",
            "Monthly Banking Fee"
        ]
    ),
    TransactionTemplate(
        description_patterns=["TRANSFER", "WIRE TRANSFER"],
        amount_range=(Decimal("100.00"), Decimal("5000.00")),
        frequency="weekly",
        transaction_type="debit",
        category="Transfers",
        description_variations=[
            "ACH TRANSFER",
            "Wire Transfer Out",
            "ONLINE TRANSFER",
            "Bank Transfer"
        ]
    ),
    TransactionTemplate(
        description_patterns=["VENDOR", "SUPPLIER"],
        amount_range=(Decimal("200.00"), Decimal("2000.00")),
        frequency="weekly",
        transaction_type="debit",
        category="Vendor Payments",
        description_variations=[
            "VENDOR PAYMENT - ABC CORP",
            "Payment to Supplier XYZ",
            "VENDOR INVOICE #12345",
            "Supplier Payment"
        ]
    ),
    TransactionTemplate(
        description_patterns=["NETFLIX", "SPOTIFY", "SUBSCRIPTION"],
        amount_range=(Decimal("9.99"), Decimal("29.99")),
        frequency="monthly",
        transaction_type="debit",
        category="Subscriptions",
        description_variations=[
            "NETFLIX MONTHLY",
            "Spotify Premium",
            "SUBSCRIPTION RENEWAL",
            "Monthly Subscription Fee"
        ]
    ),
    TransactionTemplate(
        description_patterns=["FUEL", "GAS STATION", "SHELL", "EXXON"],
        amount_range=(Decimal("30.00"), Decimal("100.00")),
        frequency="daily",
        transaction_type="debit",
        category="Fuel",
        description_variations=[
            "SHELL #1234 GAS",
            "Exxon Mobil Fuel",
            "GAS STATION PURCHASE",
            "Fuel Purchase"
        ]
    ),
]


def get_random_template() -> TransactionTemplate:
    """Get a random transaction template."""
    return random.choice(MERCHANT_TEMPLATES)


def get_template_by_category(category: str) -> TransactionTemplate:
    """Get a template matching a specific category."""
    matching = [t for t in MERCHANT_TEMPLATES if t.category == category]
    return random.choice(matching) if matching else get_random_template()


def generate_description(template: TransactionTemplate, variation_level: str = "none") -> str:
    """
    Generate a transaction description from a template.
    
    Args:
        template: Transaction template to use
        variation_level: "none", "minor", or "major" for description variation
    
    Returns:
        Generated description string
    """
    if variation_level == "none" or not template.description_variations:
        return random.choice(template.description_patterns)
    elif variation_level == "minor":
        # Use a variation but keep it similar
        return random.choice(template.description_variations[:2] if len(template.description_variations) >= 2 else template.description_variations)
    else:  # major
        # Use any variation, potentially very different
        return random.choice(template.description_variations)


def generate_amount(template: TransactionTemplate) -> Decimal:
    """Generate a random amount within the template's range."""
    min_amount, max_amount = template.amount_range
    # Generate random amount with 2 decimal places
    amount = Decimal(str(random.uniform(float(min_amount), float(max_amount))))
    return amount.quantize(Decimal("0.01"))


def should_generate_transaction(template: TransactionTemplate, days_since_start: int) -> bool:
    """
    Determine if a transaction should be generated based on frequency.
    
    Args:
        template: Transaction template
        days_since_start: Days since the start of the date range
    
    Returns:
        True if transaction should be generated
    """
    if template.frequency == "daily":
        return random.random() < 0.3  # 30% chance per day
    elif template.frequency == "weekly":
        return days_since_start % 7 == 0 or random.random() < 0.15
    elif template.frequency == "monthly":
        return days_since_start % 30 == 0 or random.random() < 0.05
    else:  # one_time
        return random.random() < 0.1  # 10% chance overall
    
    return False

