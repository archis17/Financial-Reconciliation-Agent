#!/usr/bin/env python3
"""
Test matching engine with actual test data (rule-based only).
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ingestion import IngestionService
from matching.rules import RuleBasedMatcher, MatchingConfig
from matching.scorer import ConfidenceScorer
from matching.models import Match, MatchType
from decimal import Decimal

def main():
    print("=" * 60)
    print("Testing Matching Engine with Real Data")
    print("=" * 60)
    print()
    
    # Ingest data
    print("1. Ingesting data...")
    service = IngestionService()
    
    bank_result = service.ingest_bank_statement("test_data/bank_statement.csv")
    ledger_result = service.ingest_ledger("test_data/internal_ledger.csv")
    
    print(f"   ✓ Ingested {len(bank_result.transactions)} bank transactions")
    print(f"   ✓ Ingested {len(ledger_result.transactions)} ledger transactions")
    print()
    
    # Setup matching
    print("2. Setting up matching engine...")
    config = MatchingConfig(
        amount_tolerance=Decimal("5.00"),
        date_window_days=7
    )
    rule_matcher = RuleBasedMatcher(config)
    scorer = ConfidenceScorer()
    
    print(f"   ✓ Amount tolerance: ${config.amount_tolerance}")
    print(f"   ✓ Date window: ±{config.date_window_days} days")
    print()
    
    # Perform matching
    print("3. Matching transactions...")
    matches = []
    matched_bank_ids = set()
    matched_ledger_ids = set()
    
    for bank_tx in bank_result.transactions:
        if bank_tx.id in matched_bank_ids:
            continue
        
        best_match = None
        best_confidence = 0.0
        
        for ledger_tx in ledger_result.transactions:
            if ledger_tx.id in matched_ledger_ids:
                continue
            
            # Rule-based matching
            rule_result = rule_matcher.match(bank_tx, ledger_tx)
            
            if rule_result:
                # For now, use a simple description similarity (exact match = 1.0, else 0.5)
                # In full version, this would use embeddings
                desc_sim = 1.0 if bank_tx.description.upper() == ledger_tx.description.upper() else 0.5
                
                # Calculate confidence
                confidence = scorer.calculate_confidence(
                    amount_score=rule_result["amount_score"],
                    date_score=rule_result["date_score"],
                    description_score=desc_sim,
                    reference_match=rule_result["reference_match"]
                )
                
                if confidence > best_confidence and confidence >= 0.5:
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
                match_type=MatchType.FUZZY,  # Simplified
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
    
    # Results
    print(f"   ✓ Found {len(matches)} matches")
    print()
    
    # Statistics
    print("4. Match Statistics")
    print("-" * 60)
    if matches:
        confidences = [m.confidence for m in matches]
        print(f"   Total matches: {len(matches)}")
        print(f"   Average confidence: {sum(confidences) / len(confidences):.3f}")
        print(f"   Min confidence: {min(confidences):.3f}")
        print(f"   Max confidence: {max(confidences):.3f}")
        
        # Amount differences
        amount_diffs = [abs(float(m.amount_difference)) for m in matches]
        print(f"   Average amount difference: ${sum(amount_diffs) / len(amount_diffs):.2f}")
        print(f"   Max amount difference: ${max(amount_diffs):.2f}")
        
        # Date differences
        date_diffs = [abs(m.date_difference_days) for m in matches]
        print(f"   Average date difference: {sum(date_diffs) / len(date_diffs):.1f} days")
        print(f"   Max date difference: {max(date_diffs)} days")
    
    unmatched_bank = len(bank_result.transactions) - len(matched_bank_ids)
    unmatched_ledger = len(ledger_result.transactions) - len(matched_ledger_ids)
    print(f"   Unmatched bank transactions: {unmatched_bank}")
    print(f"   Unmatched ledger transactions: {unmatched_ledger}")
    print()
    
    # Show sample matches
    print("5. Sample Matches (Top 5)")
    print("-" * 60)
    sorted_matches = sorted(matches, key=lambda m: m.confidence, reverse=True)
    for i, match in enumerate(sorted_matches[:5], 1):
        bank_tx = next(tx for tx in bank_result.transactions if tx.id == match.bank_transaction_id)
        ledger_tx = next(tx for tx in ledger_result.transactions if tx.id == match.ledger_transaction_id)
        
        print(f"\n   Match {i} (Confidence: {match.confidence:.3f}):")
        print(f"     Bank:  {bank_tx.date} | ${bank_tx.amount:10.2f} | {bank_tx.description[:35]}")
        print(f"     Ledger: {ledger_tx.date} | ${ledger_tx.amount:10.2f} | {ledger_tx.description[:35]}")
        print(f"     Diff: ${match.amount_difference:.2f} | {match.date_difference_days} days | "
              f"Scores: A={match.amount_score:.2f}, D={match.date_score:.2f}, Desc={match.description_score:.2f}")
    
    print()
    print("=" * 60)
    print("Test completed successfully!")
    print("=" * 60)
    print()
    print("Note: This test uses simplified description matching.")
    print("Full embedding-based matching requires:")
    print("  pip install numpy sentence-transformers faiss-cpu")

if __name__ == "__main__":
    main()

