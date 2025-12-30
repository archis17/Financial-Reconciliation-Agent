#!/usr/bin/env python3
"""
Test script for reporting and ticket generation.

Usage:
    python test_reporting.py [--bank-file PATH] [--ledger-file PATH]
"""

import sys
import os
import uuid
import time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import argparse
import logging
from datetime import datetime
from ingestion import IngestionService
from matching.rules import MatchingConfig
from matching.scorer import ConfidenceScorer
from matching.models import Match, MatchType, MatchResult
from discrepancy import DiscrepancyDetector
from reporting import ReconciliationReportGenerator, TicketGenerator, TicketFormat
from reporting.models import ReconciliationReport

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


def simple_match(bank_txs, ledger_txs, min_confidence=0.5):
    """Simple matching using only rule-based matcher."""
    from matching.rules import RuleBasedMatcher
    
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
    parser = argparse.ArgumentParser(description="Test reporting and ticket generation")
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
        "--output-dir",
        type=str,
        default="reports",
        help="Output directory for reports"
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("Reporting & Ticket Generation Test")
    print("=" * 60)
    print()
    
    start_time = time.time()
    reconciliation_id = str(uuid.uuid4())
    
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
    
    # 4. Create reconciliation report
    processing_time = time.time() - start_time
    
    report = ReconciliationReport(
        reconciliation_id=reconciliation_id,
        run_at=datetime.now(),
        status="completed",
        bank_transactions_count=len(bank_result.transactions),
        ledger_transactions_count=len(ledger_result.transactions),
        matched_count=len(match_result.matches),
        unmatched_bank_count=len(match_result.unmatched_bank),
        unmatched_ledger_count=len(match_result.unmatched_ledger),
        discrepancy_count=len(discrepancy_result.discrepancies),
        processing_time_seconds=processing_time
    )
    
    # 5. Generate reports
    print("4. Generating reports...")
    report_generator = ReconciliationReportGenerator(output_dir=args.output_dir)
    
    csv_path = report_generator.generate_csv_report(
        reconciliation_id,
        bank_result.transactions,
        ledger_result.transactions,
        match_result,
        discrepancy_result,
        report
    )
    print(f"   ✓ CSV Report: {csv_path}")
    
    summary_path = report_generator.generate_summary_report(
        reconciliation_id,
        report,
        match_result,
        discrepancy_result
    )
    print(f"   ✓ Summary Report: {summary_path}")
    
    readable_path = report_generator.generate_readable_report(
        reconciliation_id,
        report,
        match_result,
        discrepancy_result
    )
    print(f"   ✓ Readable Report: {readable_path}")
    print()
    
    # 6. Generate tickets
    print("5. Generating tickets...")
    ticket_generator = TicketGenerator(default_assignee="accounting-team")
    
    tickets = ticket_generator.generate_tickets_from_discrepancies(
        discrepancy_result.discrepancies,
        reconciliation_id,
        min_severity=None  # Generate tickets for all
    )
    
    print(f"   ✓ Generated {len(tickets)} tickets")
    print()
    
    # 7. Save tickets in different formats
    print("6. Saving tickets in different formats...")
    
    # Jira format
    jira_path = os.path.join(args.output_dir, f"tickets_jira_{reconciliation_id[:8]}.json")
    ticket_generator.save_tickets_json(tickets, TicketFormat.JIRA, jira_path)
    print(f"   ✓ Jira format: {jira_path}")
    
    # ServiceNow format
    servicenow_path = os.path.join(args.output_dir, f"tickets_servicenow_{reconciliation_id[:8]}.json")
    ticket_generator.save_tickets_json(tickets, TicketFormat.SERVICENOW, servicenow_path)
    print(f"   ✓ ServiceNow format: {servicenow_path}")
    
    # n8n format
    n8n_path = os.path.join(args.output_dir, f"tickets_n8n_{reconciliation_id[:8]}.json")
    ticket_generator.save_tickets_json(tickets, TicketFormat.N8N, n8n_path)
    print(f"   ✓ n8n format: {n8n_path}")
    
    # Generic format
    generic_path = os.path.join(args.output_dir, f"tickets_generic_{reconciliation_id[:8]}.json")
    ticket_generator.save_tickets_json(tickets, TicketFormat.GENERIC, generic_path)
    print(f"   ✓ Generic format: {generic_path}")
    print()
    
    # 8. Show sample ticket
    if tickets:
        print("7. Sample Ticket (Jira Format)")
        print("-" * 60)
        sample_ticket = tickets[0]
        jira_format = ticket_generator.format_for_jira(sample_ticket)
        import json
        print(json.dumps(jira_format, indent=2, default=str))
        print()
    
    print("=" * 60)
    print("Test completed successfully!")
    print("=" * 60)
    print(f"\nAll reports and tickets saved to: {args.output_dir}/")


if __name__ == "__main__":
    main()

