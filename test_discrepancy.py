#!/usr/bin/env python3
"""
Test script for discrepancy detection.

Usage:
    python test_discrepancy.py [--bank-file PATH] [--ledger-file PATH]
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import argparse
import logging
from ingestion import IngestionService
from matching.rules import MatchingConfig
from matching.engine import MatchingEngine
from discrepancy import DiscrepancyDetector

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


def main():
    parser = argparse.ArgumentParser(description="Test discrepancy detection")
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
        default=0.5,
        help="Minimum confidence threshold for matching"
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("Discrepancy Detection Test")
    print("=" * 60)
    print()
    
    # 1. Ingest data
    print("1. Ingesting data...")
    service = IngestionService()
    
    bank_result = service.ingest_bank_statement(args.bank_file)
    ledger_result = service.ingest_ledger(args.ledger_file)
    
    print(f"   ✓ Ingested {len(bank_result.transactions)} bank transactions")
    print(f"   ✓ Ingested {len(ledger_result.transactions)} ledger transactions")
    print()
    
    # 2. Match transactions
    print("2. Matching transactions...")
    config = MatchingConfig()
    engine = MatchingEngine(matching_config=config)
    
    match_result = engine.match(
        bank_result.transactions,
        ledger_result.transactions,
        min_confidence=args.min_confidence
    )
    
    print(f"   ✓ Matched {len(match_result.matches)} transactions")
    print(f"   ✓ Unmatched bank: {len(match_result.unmatched_bank)}")
    print(f"   ✓ Unmatched ledger: {len(match_result.unmatched_ledger)}")
    print()
    
    # 3. Detect discrepancies
    print("3. Detecting discrepancies...")
    detector = DiscrepancyDetector()
    
    discrepancy_result = detector.detect(
        bank_result.transactions,
        ledger_result.transactions,
        match_result
    )
    
    print(f"   ✓ Detected {len(discrepancy_result.discrepancies)} discrepancies")
    print()
    
    # 4. Display summary
    print("4. Discrepancy Summary")
    print("-" * 60)
    print(f"   Total discrepancies: {len(discrepancy_result.discrepancies)}")
    print()
    print("   By Type:")
    print(f"     Missing in ledger: {discrepancy_result.missing_in_ledger_count}")
    print(f"     Missing in bank: {discrepancy_result.missing_in_bank_count}")
    print(f"     Amount mismatches: {discrepancy_result.amount_mismatch_count}")
    print(f"     Date mismatches: {discrepancy_result.date_mismatch_count}")
    print(f"     Duplicates: {discrepancy_result.duplicate_count}")
    print(f"     Possible fraud: {discrepancy_result.possible_fraud_count}")
    print()
    print("   By Severity:")
    print(f"     Critical: {discrepancy_result.critical_count}")
    print(f"     High: {discrepancy_result.high_count}")
    print(f"     Medium: {discrepancy_result.medium_count}")
    print(f"     Low: {discrepancy_result.low_count}")
    print()
    
    # 5. Show sample discrepancies
    if discrepancy_result.discrepancies:
        print("5. Sample Discrepancies")
        print("-" * 60)
        
        # Group by severity
        critical = [d for d in discrepancy_result.discrepancies if d.severity.value == "critical"]
        high = [d for d in discrepancy_result.discrepancies if d.severity.value == "high"]
        medium = [d for d in discrepancy_result.discrepancies if d.severity.value == "medium"]
        
        # Show critical first
        for disc in (critical + high + medium)[:10]:
            print(f"\n   [{disc.severity.value.upper()}] {disc.discrepancy_type.value}")
            print(f"   Transaction: {disc.transaction_id[:8]}...")
            if disc.amount:
                print(f"   Amount: ${disc.amount:.2f}")
            if disc.date:
                print(f"   Date: {disc.date}")
            if disc.description:
                print(f"   Description: {disc.description[:50]}")
            print(f"   Reason: {disc.machine_reason}")
            if disc.amount_difference:
                print(f"   Amount difference: ${disc.amount_difference:.2f}")
            if disc.date_difference_days is not None:
                print(f"   Date difference: {disc.date_difference_days} days")
            if disc.suggested_action:
                print(f"   Suggested action: {disc.suggested_action}")
    
    print()
    print("=" * 60)
    print("Test completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()

