#!/usr/bin/env python3
"""
Simplified test for matching engine (rule-based only, no embeddings).

This tests the rule-based matching logic without requiring ML dependencies.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from decimal import Decimal
from datetime import date
import sys
import os

# Import directly to avoid embedding dependencies
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'matching'))
from rules import RuleBasedMatcher, MatchingConfig

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'ingestion'))
from models import Transaction, TransactionSource, TransactionType

def create_test_transaction(source, date_str, amount, desc, tx_type="debit", ref=None):
    """Helper to create test transactions."""
    return Transaction(
        id=f"{source}_{date_str}_{amount}",
        source=TransactionSource.BANK if source == "bank" else TransactionSource.LEDGER,
        source_file="test.csv",
        source_row=1,
        date=date.fromisoformat(date_str),
        amount=Decimal(str(amount)),
        transaction_type=TransactionType(tx_type),
        description=desc,
        original_description=desc,
        reference=ref
    )

def test_exact_match():
    """Test exact matching."""
    print("Test 1: Exact Match")
    print("-" * 60)
    
    config = MatchingConfig(amount_tolerance=Decimal("5.00"), date_window_days=7)
    matcher = RuleBasedMatcher(config)
    
    bank_tx = create_test_transaction("bank", "2024-01-15", 100.00, "AMAZON PURCHASE", "debit", "REF123")
    ledger_tx = create_test_transaction("ledger", "2024-01-15", 100.00, "AMAZON PURCHASE", "debit", "REF123")
    
    result = matcher.match(bank_tx, ledger_tx)
    
    if result:
        print(f"✓ Match found!")
        print(f"  Amount score: {result['amount_score']:.3f}")
        print(f"  Date score: {result['date_score']:.3f}")
        print(f"  Reference match: {result['reference_match']}")
        print(f"  Amount difference: ${result['amount_difference']:.2f}")
        print(f"  Date difference: {result['date_difference_days']} days")
    else:
        print("✗ No match found")
    
    print()

def test_fuzzy_amount():
    """Test fuzzy amount matching."""
    print("Test 2: Fuzzy Amount Match (within tolerance)")
    print("-" * 60)
    
    config = MatchingConfig(amount_tolerance=Decimal("5.00"), date_window_days=7)
    matcher = RuleBasedMatcher(config)
    
    bank_tx = create_test_transaction("bank", "2024-01-15", 100.00, "STARBUCKS", "debit")
    ledger_tx = create_test_transaction("ledger", "2024-01-15", 102.50, "STARBUCKS", "debit")  # $2.50 difference
    
    result = matcher.match(bank_tx, ledger_tx)
    
    if result:
        print(f"✓ Match found!")
        print(f"  Amount score: {result['amount_score']:.3f}")
        print(f"  Amount difference: ${result['amount_difference']:.2f}")
    else:
        print("✗ No match found")
    
    print()

def test_fuzzy_date():
    """Test fuzzy date matching."""
    print("Test 3: Fuzzy Date Match (within window)")
    print("-" * 60)
    
    config = MatchingConfig(amount_tolerance=Decimal("5.00"), date_window_days=7)
    matcher = RuleBasedMatcher(config)
    
    bank_tx = create_test_transaction("bank", "2024-01-15", 100.00, "PAYROLL", "credit")
    ledger_tx = create_test_transaction("ledger", "2024-01-17", 100.00, "PAYROLL", "credit")  # 2 days difference
    
    result = matcher.match(bank_tx, ledger_tx)
    
    if result:
        print(f"✓ Match found!")
        print(f"  Date score: {result['date_score']:.3f}")
        print(f"  Date difference: {result['date_difference_days']} days")
    else:
        print("✗ No match found")
    
    print()

def test_outside_tolerance():
    """Test transactions outside tolerance."""
    print("Test 4: Outside Tolerance (should not match)")
    print("-" * 60)
    
    config = MatchingConfig(amount_tolerance=Decimal("5.00"), date_window_days=7)
    matcher = RuleBasedMatcher(config)
    
    bank_tx = create_test_transaction("bank", "2024-01-15", 100.00, "VENDOR PAYMENT", "debit")
    ledger_tx = create_test_transaction("ledger", "2024-01-25", 100.00, "VENDOR PAYMENT", "debit")  # 10 days (outside window)
    
    result = matcher.match(bank_tx, ledger_tx)
    
    if result:
        print(f"✗ Unexpected match found!")
    else:
        print(f"✓ Correctly rejected (date outside window)")
    
    print()

def test_different_type():
    """Test transactions with different types."""
    print("Test 5: Different Transaction Type (should not match)")
    print("-" * 60)
    
    config = MatchingConfig(amount_tolerance=Decimal("5.00"), date_window_days=7, require_same_type=True)
    matcher = RuleBasedMatcher(config)
    
    bank_tx = create_test_transaction("bank", "2024-01-15", 100.00, "PAYMENT", "debit")
    ledger_tx = create_test_transaction("ledger", "2024-01-15", 100.00, "PAYMENT", "credit")  # Different type
    
    result = matcher.match(bank_tx, ledger_tx)
    
    if result:
        print(f"✗ Unexpected match found!")
    else:
        print(f"✓ Correctly rejected (different transaction types)")
    
    print()

def test_amount_scoring():
    """Test amount scoring logic."""
    print("Test 6: Amount Scoring Logic")
    print("-" * 60)
    
    config = MatchingConfig(amount_tolerance=Decimal("5.00"), date_window_days=7)
    matcher = RuleBasedMatcher(config)
    
    test_cases = [
        (100.00, 100.00, "Exact match"),
        (100.00, 102.00, "$2 difference"),
        (100.00, 104.00, "$4 difference"),
        (100.00, 105.00, "$5 difference (at tolerance)"),
        (100.00, 106.00, "$6 difference (outside tolerance)"),
    ]
    
    for bank_amt, ledger_amt, desc in test_cases:
        score, diff = matcher.calculate_amount_score(Decimal(str(bank_amt)), Decimal(str(ledger_amt)))
        print(f"  {desc:30s} | Score: {score:.3f} | Diff: ${diff:.2f}")
    
    print()

def test_date_scoring():
    """Test date scoring logic."""
    print("Test 7: Date Scoring Logic")
    print("-" * 60)
    
    config = MatchingConfig(amount_tolerance=Decimal("5.00"), date_window_days=7)
    matcher = RuleBasedMatcher(config)
    
    base_date = date(2024, 1, 15)
    test_cases = [
        (0, "Same day"),
        (1, "1 day difference"),
        (3, "3 days difference"),
        (5, "5 days difference"),
        (7, "7 days (at window limit)"),
        (8, "8 days (outside window)"),
    ]
    
    for days_diff, desc in test_cases:
        other_date = date(2024, 1, 15 + days_diff)
        score, diff = matcher.calculate_date_score(base_date, other_date)
        print(f"  {desc:30s} | Score: {score:.3f} | Diff: {diff} days")
    
    print()

def main():
    print("=" * 60)
    print("Rule-Based Matching Engine Tests")
    print("=" * 60)
    print()
    
    test_exact_match()
    test_fuzzy_amount()
    test_fuzzy_date()
    test_outside_tolerance()
    test_different_type()
    test_amount_scoring()
    test_date_scoring()
    
    print("=" * 60)
    print("All rule-based tests completed!")
    print("=" * 60)
    print()
    print("Note: Embedding-based matching requires:")
    print("  - numpy")
    print("  - sentence-transformers")
    print("  - faiss-cpu")
    print()
    print("Install with: pip install -r requirements.txt")

if __name__ == "__main__":
    main()

