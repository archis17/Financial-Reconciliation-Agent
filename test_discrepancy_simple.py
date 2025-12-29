#!/usr/bin/env python3
"""
Test script for discrepancy detection (using rule-based matching only).

Usage:
    python test_discrepancy_simple.py [--bank-file PATH] [--ledger-file PATH]
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import argparse
import logging
from decimal import Decimal
from ingestion import IngestionService
from matching.rules import RuleBasedMatcher, MatchingConfig
from matching.scorer import ConfidenceScorer
from matching.models import Match, MatchType, MatchResult
from discrepancy import DiscrepancyDetector

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


def simple_match(bank_txs, ledger_txs, min_confidence=0.5):
    """Simple matching using only rule-based matcher."""
    config = MatchingConfig()
    rule_matcher = RuleBasedMatcher(config)
    scorer = ConfidenceScorer()
    
    matches = []
    matched_bank_ids = set()
    matched_ledger_ids = set()
    
    for bank_tx in bank_txs:
        if bank_tx.id in matched_bank_ids:
            continue
        
        best_match = None
        best_confidence = 0.0
        
        for ledger_tx in ledger_txs:
            if ledger_tx.id in matched_ledger_ids:
                continue
            
            rule_result = rule_matcher.match(bank_tx, ledger_tx)
            
            if rule_result:
                # Simple description similarity (exact match = 1.0, else 0.5)
                desc_sim = 1.0 if bank_tx.description.upper() == ledger_tx.description.upper() else 0.5
                
                confidence = scorer.calculate_confidence(
                    amount_score=rule_result["amount_score"],
                    date_score=rule_result["date_score"],
                    description_score=desc_sim,
                    reference_match=rule_result["reference_match"]
                )
                
                if confidence > best_confidence and confidence >= min_confidence:
                    best_confidence = confidence
                    best_match = {
                        "ledger_tx": ledger_tx,
                        "confidence": confidence,
                        "amount_score": rule_result["amount_score"],
                        "date_score": rule_result["date_score"],
                        "description_score": desc_sim,
                        "reference_match": rule_result["reference_match"],
                        "amount_difference": rule_result["amount_difference"],
                        "date_difference_days": rule_result["date_difference_days"],
                    }
        
        if best_match:
            match = Match(
                bank_transaction_id=bank_tx.id,
                ledger_transaction_id=best_match["ledger_tx"].id,
                confidence=best_match["confidence"],
                match_type=MatchType.FUZZY,
                amount_difference=best_match["amount_difference"],
                date_difference_days=best_match["date_difference_days"],
                description_similarity=best_match["description_score"],
                reference_match=best_match["reference_match"],
                amount_score=best_match["amount_score"],
                date_score=best_match["date_score"],
                description_score=best_match["description_score"],
                reference_score=1.0 if best_match["reference_match"] else 0.0,
            )
            matches.append(match)
            matched_bank_ids.add(bank_tx.id)
            matched_ledger_ids.add(best_match["ledger_tx"].id)
    
    unmatched_bank = [tx.id for tx in bank_txs if tx.id not in matched_bank_ids]
    unmatched_ledger = [tx.id for tx in ledger_txs if tx.id not in matched_ledger_ids]
    
    return MatchResult(
        matches=matches,
        unmatched_bank=unmatched_bank,
        unmatched_ledger=unmatched_ledger
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
    match_result = simple_match(
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

