"""
Reconciliation report generation.
"""

import csv
import json
import logging
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path

from ingestion.models import Transaction
from matching.models import Match, MatchResult
from discrepancy.models import Discrepancy, DiscrepancyResult
from reporting.models import ReconciliationReport

logger = logging.getLogger(__name__)


class ReconciliationReportGenerator:
    """Generates reconciliation reports in various formats."""
    
    def __init__(self, output_dir: str = "reports"):
        """
        Initialize report generator.
        
        Args:
            output_dir: Directory to save reports
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
    
    def generate_csv_report(
        self,
        reconciliation_id: str,
        bank_transactions: List[Transaction],
        ledger_transactions: List[Transaction],
        match_result: MatchResult,
        discrepancy_result: DiscrepancyResult,
        report: ReconciliationReport
    ) -> str:
        """
        Generate CSV reconciliation report.
        
        Returns:
            Path to generated CSV file
        """
        filename = f"reconciliation_report_{reconciliation_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        filepath = self.output_dir / filename
        
        # Create lookup dictionaries
        bank_tx_dict = {tx.id: tx for tx in bank_transactions}
        ledger_tx_dict = {tx.id: tx for tx in ledger_transactions}
        match_dict = {m.bank_transaction_id: m for m in match_result.matches}
        discrepancy_dict = {d.transaction_id: d for d in discrepancy_result.discrepancies}
        
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Header
            writer.writerow([
                "Transaction ID",
                "Source",
                "Date",
                "Amount",
                "Type",
                "Description",
                "Match Status",
                "Matched With",
                "Match Confidence",
                "Discrepancy Type",
                "Severity",
                "Machine Reason",
                "LLM Explanation",
                "Suggested Action"
            ])
            
            # Process bank transactions
            for tx in bank_transactions:
                match = match_dict.get(tx.id)
                disc = discrepancy_dict.get(tx.id)
                
                row = [
                    tx.id[:8],  # Short ID
                    "Bank",
                    tx.date.isoformat() if tx.date else "",
                    str(tx.amount),
                    tx.transaction_type.value,
                    tx.description,
                    "Matched" if match else "Unmatched",
                    match.ledger_transaction_id[:8] if match else "",
                    f"{match.confidence:.3f}" if match else "",
                    disc.discrepancy_type.value if disc else "",
                    disc.severity.value if disc else "",
                    disc.machine_reason if disc else "",
                    disc.llm_explanation if disc and disc.llm_explanation else "",
                    disc.suggested_action if disc else "",
                ]
                writer.writerow(row)
            
            # Process ledger transactions (only unmatched)
            for tx in ledger_transactions:
                # Only include if not matched
                if tx.id not in [m.ledger_transaction_id for m in match_result.matches]:
                    disc = discrepancy_dict.get(tx.id)
                    
                    row = [
                        tx.id[:8],
                        "Ledger",
                        tx.date.isoformat() if tx.date else "",
                        str(tx.amount),
                        tx.transaction_type.value,
                        tx.description,
                        "Unmatched",
                        "",
                        "",
                        disc.discrepancy_type.value if disc else "",
                        disc.severity.value if disc else "",
                        disc.machine_reason if disc else "",
                        disc.llm_explanation if disc and disc.llm_explanation else "",
                        disc.suggested_action if disc else "",
                    ]
                    writer.writerow(row)
        
        logger.info(f"Generated CSV report: {filepath}")
        return str(filepath)
    
    def generate_summary_report(
        self,
        reconciliation_id: str,
        report: ReconciliationReport,
        match_result: MatchResult,
        discrepancy_result: DiscrepancyResult
    ) -> str:
        """
        Generate summary report (JSON format).
        
        Returns:
            Path to generated JSON file
        """
        filename = f"reconciliation_summary_{reconciliation_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = self.output_dir / filename
        
        summary = {
            "reconciliation": report.to_dict(),
            "matching": {
                "total_matches": len(match_result.matches),
                "unmatched_bank": len(match_result.unmatched_bank),
                "unmatched_ledger": len(match_result.unmatched_ledger),
                "match_rate": len(match_result.matches) / report.bank_transactions_count if report.bank_transactions_count > 0 else 0.0,
            },
            "discrepancies": discrepancy_result.to_dict(),
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, default=str)
        
        logger.info(f"Generated summary report: {filepath}")
        return str(filepath)
    
    def generate_readable_report(
        self,
        reconciliation_id: str,
        report: ReconciliationReport,
        match_result: MatchResult,
        discrepancy_result: DiscrepancyResult
    ) -> str:
        """
        Generate human-readable text report.
        
        Returns:
            Path to generated text file
        """
        filename = f"reconciliation_readable_{reconciliation_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        filepath = self.output_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("FINANCIAL RECONCILIATION REPORT\n")
            f.write("=" * 80 + "\n\n")
            
            f.write(f"Reconciliation ID: {reconciliation_id}\n")
            f.write(f"Run Date: {report.run_at.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Status: {report.status}\n\n")
            
            f.write("SUMMARY\n")
            f.write("-" * 80 + "\n")
            f.write(f"Bank Transactions: {report.bank_transactions_count}\n")
            f.write(f"Ledger Transactions: {report.ledger_transactions_count}\n")
            f.write(f"Matched: {report.matched_count}\n")
            f.write(f"Unmatched (Bank): {report.unmatched_bank_count}\n")
            f.write(f"Unmatched (Ledger): {report.unmatched_ledger_count}\n")
            f.write(f"Discrepancies: {report.discrepancy_count}\n")
            f.write(f"Processing Time: {report.processing_time_seconds:.2f} seconds\n")
            
            if report.llm_calls_made > 0:
                f.write(f"LLM Calls: {report.llm_calls_made}\n")
                f.write(f"LLM Tokens Used: {report.llm_tokens_used}\n")
            
            f.write("\n")
            
            # Discrepancies by severity
            f.write("DISCREPANCIES BY SEVERITY\n")
            f.write("-" * 80 + "\n")
            f.write(f"Critical: {discrepancy_result.critical_count}\n")
            f.write(f"High: {discrepancy_result.high_count}\n")
            f.write(f"Medium: {discrepancy_result.medium_count}\n")
            f.write(f"Low: {discrepancy_result.low_count}\n\n")
            
            # Discrepancies by type
            f.write("DISCREPANCIES BY TYPE\n")
            f.write("-" * 80 + "\n")
            f.write(f"Missing in Ledger: {discrepancy_result.missing_in_ledger_count}\n")
            f.write(f"Missing in Bank: {discrepancy_result.missing_in_bank_count}\n")
            f.write(f"Amount Mismatches: {discrepancy_result.amount_mismatch_count}\n")
            f.write(f"Date Mismatches: {discrepancy_result.date_mismatch_count}\n")
            f.write(f"Duplicates: {discrepancy_result.duplicate_count}\n")
            f.write(f"Possible Fraud: {discrepancy_result.possible_fraud_count}\n\n")
            
            # Critical discrepancies
            critical = [d for d in discrepancy_result.discrepancies if d.severity.value == "critical"]
            if critical:
                f.write("CRITICAL DISCREPANCIES\n")
                f.write("-" * 80 + "\n")
                for disc in critical[:10]:  # Limit to 10
                    f.write(f"\n[{disc.severity.value.upper()}] {disc.discrepancy_type.value}\n")
                    f.write(f"Transaction: {disc.description} (${disc.amount})\n")
                    f.write(f"Reason: {disc.machine_reason}\n")
                    if disc.llm_explanation:
                        f.write(f"Explanation: {disc.llm_explanation}\n")
                    if disc.suggested_action:
                        f.write(f"Action: {disc.suggested_action}\n")
                f.write("\n")
        
        logger.info(f"Generated readable report: {filepath}")
        return str(filepath)

