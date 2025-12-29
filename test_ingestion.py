#!/usr/bin/env python3
"""
Test script for data ingestion and normalization.

Usage:
    python test_ingestion.py [--bank-file PATH] [--ledger-file PATH]
"""

import argparse
import json
import logging
from ingestion import IngestionService

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


def main():
    parser = argparse.ArgumentParser(description="Test data ingestion")
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
        "--strict",
        action="store_true",
        help="Use strict validation (treat warnings as errors)"
    )
    
    args = parser.parse_args()
    
    service = IngestionService(strict_validation=args.strict)
    
    # Ingest bank statement
    print(f"\n{'='*60}")
    print("Ingesting Bank Statement")
    print(f"{'='*60}")
    bank_result = service.ingest_bank_statement(args.bank_file)
    
    print(f"\nBank Statement Results:")
    print(f"  Transactions ingested: {len(bank_result.transactions)}")
    print(f"  Errors: {len(bank_result.errors)}")
    print(f"  Warnings: {len(bank_result.warnings)}")
    print(f"\nStatistics:")
    stats = bank_result.stats
    print(f"  Date range: {stats.get('date_range', {}).get('min')} to {stats.get('date_range', {}).get('max')}")
    print(f"  Amount range: ${stats.get('amount_range', {}).get('min')} to ${stats.get('amount_range', {}).get('max')}")
    print(f"  Debits: {stats.get('total_debits', 0)} (${stats.get('total_debit_amount', '0.00')})")
    print(f"  Credits: {stats.get('total_credits', 0)} (${stats.get('total_credit_amount', '0.00')})")
    
    if bank_result.errors:
        print(f"\nErrors:")
        for error in bank_result.errors[:5]:  # Show first 5
            print(f"  - {error}")
    
    # Ingest ledger
    print(f"\n{'='*60}")
    print("Ingesting Internal Ledger")
    print(f"{'='*60}")
    ledger_result = service.ingest_ledger(args.ledger_file)
    
    print(f"\nLedger Results:")
    print(f"  Transactions ingested: {len(ledger_result.transactions)}")
    print(f"  Errors: {len(ledger_result.errors)}")
    print(f"  Warnings: {len(ledger_result.warnings)}")
    print(f"\nStatistics:")
    stats = ledger_result.stats
    print(f"  Date range: {stats.get('date_range', {}).get('min')} to {stats.get('date_range', {}).get('max')}")
    print(f"  Amount range: ${stats.get('amount_range', {}).get('min')} to ${stats.get('amount_range', {}).get('max')}")
    print(f"  Debits: {stats.get('total_debits', 0)} (${stats.get('total_debit_amount', '0.00')})")
    print(f"  Credits: {stats.get('total_credits', 0)} (${stats.get('total_credit_amount', '0.00')})")
    
    if ledger_result.errors:
        print(f"\nErrors:")
        for error in ledger_result.errors[:5]:  # Show first 5
            print(f"  - {error}")
    
    # Show sample transactions
    print(f"\n{'='*60}")
    print("Sample Transactions")
    print(f"{'='*60}")
    
    if bank_result.transactions:
        print("\nBank Statement (first 3):")
        for tx in bank_result.transactions[:3]:
            print(f"  {tx.date} | {tx.transaction_type.value:6s} | ${tx.amount:10.2f} | {tx.description[:50]}")
    
    if ledger_result.transactions:
        print("\nLedger (first 3):")
        for tx in ledger_result.transactions[:3]:
            print(f"  {tx.date} | {tx.transaction_type.value:6s} | ${tx.amount:10.2f} | {tx.description[:50]}")


if __name__ == "__main__":
    main()

