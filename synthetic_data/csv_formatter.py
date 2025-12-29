"""
CSV formatting for bank statements and internal ledgers.
"""

from decimal import Decimal
from datetime import date
from typing import List, Dict
import csv
from dataclasses import dataclass


@dataclass
class TransactionRow:
    """Represents a single transaction row for CSV output."""
    date: date
    description: str
    amount: Decimal
    transaction_type: str  # "debit" | "credit"
    reference: str = ""
    balance: Decimal = None  # For bank statements
    account: str = ""  # For ledger
    posting_date: date = None  # For ledger


class BankStatementFormatter:
    """Formats transactions as bank statement CSV."""
    
    @staticmethod
    def format(transactions: List[TransactionRow]) -> List[List[str]]:
        """
        Format transactions as bank statement CSV rows.
        
        Bank statement format:
        Date,Description,Debit,Credit,Balance,Reference
        """
        rows = [["Date", "Description", "Debit", "Credit", "Balance", "Reference"]]
        
        running_balance = Decimal("10000.00")  # Starting balance
        
        for tx in transactions:
            row = [
                tx.date.isoformat(),
                tx.description,
                str(abs(tx.amount)) if tx.transaction_type == "debit" else "",
                str(abs(tx.amount)) if tx.transaction_type == "credit" else "",
                str(running_balance),
                tx.reference
            ]
            
            # Update running balance
            if tx.transaction_type == "debit":
                running_balance -= tx.amount
            else:
                running_balance += tx.amount
            
            rows.append(row)
        
        return rows
    
    @staticmethod
    def save(transactions: List[TransactionRow], filepath: str):
        """Save bank statement to CSV file."""
        rows = BankStatementFormatter.format(transactions)
        
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerows(rows)


class LedgerFormatter:
    """Formats transactions as internal ledger CSV."""
    
    @staticmethod
    def format(transactions: List[TransactionRow]) -> List[List[str]]:
        """
        Format transactions as ledger CSV rows.
        
        Ledger format:
        Transaction Date,Posting Date,Description,Amount,Type,Reference,Account
        """
        rows = [["Transaction Date", "Posting Date", "Description", "Amount", "Type", "Reference", "Account"]]
        
        for tx in transactions:
            posting_date = tx.posting_date if tx.posting_date else tx.date
            
            row = [
                tx.date.isoformat(),
                posting_date.isoformat(),
                tx.description,
                str(abs(tx.amount)),
                tx.transaction_type.title(),
                tx.reference,
                tx.account
            ]
            
            rows.append(row)
        
        return rows
    
    @staticmethod
    def save(transactions: List[TransactionRow], filepath: str):
        """Save ledger to CSV file."""
        rows = LedgerFormatter.format(transactions)
        
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerows(rows)

