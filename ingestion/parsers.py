"""
CSV parsers for bank statements and ledgers.
"""

import csv
from dataclasses import dataclass
from typing import List, Dict, Optional, Callable
from decimal import Decimal
import logging

from .models import Transaction, TransactionSource, TransactionType
from .normalizers import DateNormalizer, AmountNormalizer, DescriptionNormalizer

logger = logging.getLogger(__name__)


@dataclass
class ColumnMapping:
    """Maps CSV columns to transaction fields."""
    date: Optional[str] = None
    description: Optional[str] = None
    amount: Optional[str] = None
    debit: Optional[str] = None
    credit: Optional[str] = None
    transaction_type: Optional[str] = None
    reference: Optional[str] = None
    balance: Optional[str] = None
    account: Optional[str] = None
    posting_date: Optional[str] = None
    
    @classmethod
    def auto_detect(cls, header_row: List[str]) -> 'ColumnMapping':
        """
        Auto-detect column mapping from header row.
        
        Args:
            header_row: List of column names from CSV header
        
        Returns:
            ColumnMapping with detected columns
        """
        header_lower = [col.lower().strip() for col in header_row]
        
        mapping = cls()
        
        # Date columns
        for i, col in enumerate(header_lower):
            if any(term in col for term in ["date", "transaction date", "posting date"]):
                if "posting" in col:
                    mapping.posting_date = header_row[i]
                else:
                    mapping.date = header_row[i]
        
        # Description columns
        for i, col in enumerate(header_lower):
            if any(term in col for term in ["description", "memo", "details", "narration", "payee"]):
                mapping.description = header_row[i]
                break
        
        # Amount columns
        for i, col in enumerate(header_lower):
            if "amount" in col and "debit" not in col and "credit" not in col:
                mapping.amount = header_row[i]
        
        # Debit/Credit columns
        for i, col in enumerate(header_lower):
            if "debit" in col:
                mapping.debit = header_row[i]
            elif "credit" in col:
                mapping.credit = header_row[i]
        
        # Transaction type
        for i, col in enumerate(header_lower):
            if any(term in col for term in ["type", "transaction type", "category"]):
                mapping.transaction_type = header_row[i]
        
        # Reference
        for i, col in enumerate(header_lower):
            if any(term in col for term in ["reference", "ref", "check", "check number", "transaction id"]):
                mapping.reference = header_row[i]
                break
        
        # Balance
        for i, col in enumerate(header_lower):
            if "balance" in col:
                mapping.balance = header_row[i]
        
        # Account
        for i, col in enumerate(header_lower):
            if "account" in col:
                mapping.account = header_row[i]
        
        return mapping


class BaseParser:
    """Base class for CSV parsers."""
    
    def __init__(self, source: TransactionSource, column_mapping: Optional[ColumnMapping] = None):
        self.source = source
        self.column_mapping = column_mapping
    
    def parse_file(self, filepath: str) -> List[Transaction]:
        """
        Parse a CSV file.
        
        Args:
            filepath: Path to CSV file
        
        Returns:
            List of parsed transactions
        """
        transactions = []
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                # Try to detect encoding
                reader = csv.DictReader(f)
                
                # Auto-detect column mapping if not provided
                if not self.column_mapping:
                    # Reset file pointer and read header
                    f.seek(0)
                    header = next(csv.reader(f))
                    self.column_mapping = ColumnMapping.auto_detect(header)
                    f.seek(0)
                    reader = csv.DictReader(f)
                
                # Parse each row
                for row_num, row in enumerate(reader, start=2):  # Start at 2 (header is row 1)
                    try:
                        tx = self._parse_row(row, row_num, filepath)
                        if tx:
                            transactions.append(tx)
                    except Exception as e:
                        logger.warning(f"Error parsing row {row_num} in {filepath}: {e}")
                        continue
        
        except Exception as e:
            logger.error(f"Error reading file {filepath}: {e}")
            raise
        
        return transactions
    
    def _parse_row(self, row: Dict[str, str], row_num: int, filepath: str) -> Optional[Transaction]:
        """Parse a single row. Override in subclasses."""
        raise NotImplementedError


class BankStatementParser(BaseParser):
    """Parser for bank statement CSV files."""
    
    def __init__(self, column_mapping: Optional[ColumnMapping] = None):
        super().__init__(TransactionSource.BANK, column_mapping)
    
    def _parse_row(self, row: Dict[str, str], row_num: int, filepath: str) -> Optional[Transaction]:
        """Parse a bank statement row."""
        mapping = self.column_mapping
        
        # Extract fields
        date_str = row.get(mapping.date, "") if mapping.date else ""
        description_str = row.get(mapping.description, "") if mapping.description else ""
        amount_str = row.get(mapping.amount, "") if mapping.amount else ""
        debit_str = row.get(mapping.debit, "") if mapping.debit else ""
        credit_str = row.get(mapping.credit, "") if mapping.credit else ""
        reference_str = row.get(mapping.reference, "") if mapping.reference else ""
        
        # Normalize date
        date_obj = DateNormalizer.normalize(date_str)
        if not date_obj:
            logger.warning(f"Row {row_num}: Could not parse date '{date_str}'")
            return None
        
        # Normalize amount and type
        amount, tx_type = AmountNormalizer.normalize(
            amount_str=amount_str,
            debit_amount=debit_str,
            credit_amount=credit_str
        )
        
        if amount == Decimal("0.00"):
            logger.warning(f"Row {row_num}: Zero amount, skipping")
            return None
        
        # Normalize description
        description, original_description = DescriptionNormalizer.normalize(description_str)
        
        # Create transaction
        transaction = Transaction(
            source=self.source,
            source_file=filepath,
            source_row=row_num,
            date=date_obj,
            amount=amount,
            transaction_type=TransactionType(tx_type),
            description=description,
            original_description=original_description,
            reference=reference_str if reference_str else None,
            currency="USD"  # Default, can be enhanced
        )
        
        return transaction


class LedgerParser(BaseParser):
    """Parser for internal ledger CSV files."""
    
    def __init__(self, column_mapping: Optional[ColumnMapping] = None):
        super().__init__(TransactionSource.LEDGER, column_mapping)
    
    def _parse_row(self, row: Dict[str, str], row_num: int, filepath: str) -> Optional[Transaction]:
        """Parse a ledger row."""
        mapping = self.column_mapping
        
        # Extract fields
        date_str = row.get(mapping.date, "") if mapping.date else ""
        posting_date_str = row.get(mapping.posting_date, "") if mapping.posting_date else ""
        description_str = row.get(mapping.description, "") if mapping.description else ""
        amount_str = row.get(mapping.amount, "") if mapping.amount else ""
        tx_type_str = row.get(mapping.transaction_type, "") if mapping.transaction_type else ""
        reference_str = row.get(mapping.reference, "") if mapping.reference else ""
        account_str = row.get(mapping.account, "") if mapping.account else ""
        
        # Use posting date if available, otherwise transaction date
        effective_date_str = posting_date_str if posting_date_str else date_str
        
        # Normalize date
        date_obj = DateNormalizer.normalize(effective_date_str)
        if not date_obj:
            logger.warning(f"Row {row_num}: Could not parse date '{effective_date_str}'")
            return None
        
        # Normalize amount and type
        amount, tx_type = AmountNormalizer.normalize(
            amount_str=amount_str,
            transaction_type_str=tx_type_str
        )
        
        if amount == Decimal("0.00"):
            logger.warning(f"Row {row_num}: Zero amount, skipping")
            return None
        
        # Normalize description
        description, original_description = DescriptionNormalizer.normalize(description_str)
        
        # Create transaction
        transaction = Transaction(
            source=self.source,
            source_file=filepath,
            source_row=row_num,
            date=date_obj,
            amount=amount,
            transaction_type=TransactionType(tx_type),
            description=description,
            original_description=original_description,
            reference=reference_str if reference_str else None,
            category=account_str if account_str else None,
            currency="USD"  # Default, can be enhanced
        )
        
        return transaction

