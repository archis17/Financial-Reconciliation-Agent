#!/usr/bin/env python3
"""
Test script for matching engine.

Usage:
    python test_matching.py [--bank-file PATH] [--ledger-file PATH]
"""

import argparse
import json
import logging
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ingestion import IngestionService
from matching import MatchingEngine, MatchingConfig

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


def main():
    parser = argparse.ArgumentParser(description="Test matching engine")
    parser.add_argument(
        "--bank-file",
        type=str,
        default="test_data/bank_statement.csv",
        help="Path to bank statement CSV"
    )
    parser.add_argument(
        "--ledger-file",
        type=str,
        default="test_data/internal_ledger.csv",
        help="Path to ledger CSV"
    )
    parser.add_argument(
        "--min-confidence",
        type=float,
        default=0.6,
        help="Minimum confidence threshold (0.0-1.0)"
    )
    parser.add_argument(
        "--amount-tolerance",
        type=float,
        default=5.00,
        help="Amount tolerance in dollars"
    )
    parser.add_argument(
        "--date-window",
        type=int,
        default=7,
        help="Date window in days"
    )
    
    args = parser.parse_args()
    
    # Ingest data
    print("Ingesting data...")
    ingestion_service = IngestionService()
    
    bank_result = ingestion_service.ingest_bank_statement(args.bank_file)
    ledger_result = ingestion_service.ingest_ledger(args.ledger_file)
    
    print(f"Ingested {len(bank_result.transactions)} bank transactions")
    print(f"Ingested {len(ledger_result.transactions)} ledger transactions")
    
    # Configure matching
    matching_config = MatchingConfig(
        amount_tolerance=args.amount_tolerance,
        date_window_days=args.date_window
    )
    
    # Create matching engine
    print("\nInitializing matching engine...")
    engine = MatchingEngine(matching_config=matching_config)
    
    # Perform matching
    print(f"\nMatching transactions (min confidence: {args.min_confidence})...")
    match_result = engine.match(
        bank_result.transactions,
        ledger_result.transactions,
        min_confidence=args.min_confidence
    )
    
    # Display results
    print(f"\n{'='*60}")
    print("Matching Results")
    print(f"{'='*60}")
    print(f"Matches found: {len(match_result.matches)}")
    print(f"Unmatched bank transactions: {len(match_result.unmatched_bank)}")
    print(f"Unmatched ledger transactions: {len(match_result.unmatched_ledger)}")
    
    # Match statistics
    if match_result.matches:
        confidences = [m.confidence for m in match_result.matches]
        match_types = {}
        for m in match_result.matches:
            match_types[m.match_type.value] = match_types.get(m.match_type.value, 0) + 1
        
        print(f"\nMatch Statistics:")
        print(f"  Average confidence: {sum(confidences) / len(confidences):.3f}")
        print(f"  Min confidence: {min(confidences):.3f}")
        print(f"  Max confidence: {max(confidences):.3f}")
        print(f"\nMatch Types:")
        for match_type, count in match_types.items():
            print(f"  {match_type}: {count}")
    
    # Show sample matches
    print(f"\n{'='*60}")
    print("Sample Matches (Top 5 by Confidence)")
    print(f"{'='*60}")
    
    sorted_matches = sorted(match_result.matches, key=lambda m: m.confidence, reverse=True)
    for i, match in enumerate(sorted_matches[:5], 1):
        # Find transactions
        bank_tx = next(tx for tx in bank_result.transactions if tx.id == match.bank_transaction_id)
        ledger_tx = next(tx for tx in ledger_result.transactions if tx.id == match.ledger_transaction_id)
        
        print(f"\nMatch {i}:")
        print(f"  Confidence: {match.confidence:.3f} ({match.match_type.value})")
        print(f"  Bank:  {bank_tx.date} | ${bank_tx.amount:10.2f} | {bank_tx.description[:40]}")
        print(f"  Ledger: {ledger_tx.date} | ${ledger_tx.amount:10.2f} | {ledger_tx.description[:40]}")
        print(f"  Amount diff: ${match.amount_difference:.2f} | Date diff: {match.date_difference_days} days")
        print(f"  Scores: Amount={match.amount_score:.2f}, Date={match.date_score:.2f}, Desc={match.description_score:.2f}")
    
    # Show unmatched
    if match_result.unmatched_bank:
        print(f"\n{'='*60}")
        print(f"Unmatched Bank Transactions ({len(match_result.unmatched_bank)})")
        print(f"{'='*60}")
        for tx_id in match_result.unmatched_bank[:5]:
            tx = next(tx for tx in bank_result.transactions if tx.id == tx_id)
            print(f"  {tx.date} | ${tx.amount:10.2f} | {tx.description[:50]}")
    
    if match_result.unmatched_ledger:
        print(f"\n{'='*60}")
        print(f"Unmatched Ledger Transactions ({len(match_result.unmatched_ledger)})")
        print(f"{'='*60}")
        for tx_id in match_result.unmatched_ledger[:5]:
            tx = next(tx for tx in ledger_result.transactions if tx.id == tx_id)
            print(f"  {tx.date} | ${tx.amount:10.2f} | {tx.description[:50]}")


if __name__ == "__main__":
    main()

