#!/usr/bin/env python3
"""
Test script for LLM explanation layer.

Usage:
    python test_llm_explanations.py [--bank-file PATH] [--ledger-file PATH] [--no-llm]
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import argparse
import logging
from ingestion import IngestionService
from matching.rules import MatchingConfig
from matching.engine import MatchingEngine
from discrepancy import DiscrepancyDetector, DiscrepancyLLMIntegrator
from llm_service import LLMExplanationService

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


def simple_match(bank_txs, ledger_txs, min_confidence=0.5):
    """Simple matching using only rule-based matcher."""
    from matching.rules import RuleBasedMatcher
    from matching.scorer import ConfidenceScorer
    from matching.models import Match, MatchType, MatchResult
    
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
    parser = argparse.ArgumentParser(description="Test LLM explanations")
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
        "--no-llm",
        action="store_true",
        help="Disable LLM explanations (use machine-readable only)"
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("LLM Explanation Layer Test")
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
        ledger_result.transactions
    )
    
    print(f"   ✓ Matched {len(match_result.matches)} transactions")
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
    
    # 4. Enhance with LLM explanations
    if not args.no_llm:
        print("4. Generating LLM explanations...")
        try:
            llm_service = LLMExplanationService()
            integrator = DiscrepancyLLMIntegrator(llm_service=llm_service, enable_llm=True)
            
            # Create transaction dictionaries for context
            bank_tx_dict = {tx.id: tx for tx in bank_result.transactions}
            ledger_tx_dict = {tx.id: tx for tx in ledger_result.transactions}
            
            # Enhance discrepancies
            enhanced_discrepancies = integrator.enhance_with_explanations(
                discrepancy_result.discrepancies,
                bank_tx_dict=bank_tx_dict,
                ledger_tx_dict=ledger_tx_dict
            )
            
            # Update result
            discrepancy_result.discrepancies = enhanced_discrepancies
            
            # Show usage stats
            stats = llm_service.get_usage_stats()
            print(f"   ✓ Generated {stats['total_requests']} explanations")
            print(f"   ✓ Tokens used: {stats['total_tokens_used']}")
            print(f"   ✓ Estimated cost: ${stats['estimated_cost_usd']:.4f}")
            print()
        except Exception as e:
            print(f"   ⚠ LLM service error: {e}")
            print("   Continuing with machine-readable explanations only")
            print()
    else:
        print("4. LLM explanations disabled (using machine-readable only)")
        print()
    
    # 5. Display enhanced discrepancies
    if discrepancy_result.discrepancies:
        print("5. Discrepancies with Explanations")
        print("-" * 60)
        
        for i, disc in enumerate(discrepancy_result.discrepancies[:5], 1):
            print(f"\nDiscrepancy {i}: [{disc.severity.value.upper()}] {disc.discrepancy_type.value}")
            print(f"  Transaction: {disc.description} (${disc.amount})")
            print(f"  Machine Reason: {disc.machine_reason}")
            
            if disc.llm_explanation:
                print(f"\n  LLM Explanation:")
                print(f"  {disc.llm_explanation}")
            
            if disc.suggested_action:
                print(f"\n  Suggested Action:")
                print(f"  {disc.suggested_action}")
    
    print()
    print("=" * 60)
    print("Test completed!")
    print("=" * 60)
    
    if args.no_llm:
        print("\nNote: Run without --no-llm to test LLM explanations")
        print("      (requires OPENAI_API_KEY environment variable)")


if __name__ == "__main__":
    main()

