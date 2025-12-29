"""
Main ingestion service orchestrating parsing, normalization, and validation.
"""

from typing import List, Dict, Optional
import logging

from .models import Transaction, TransactionSource
from .parsers import BankStatementParser, LedgerParser, ColumnMapping
from .validators import TransactionValidator, ValidationError

logger = logging.getLogger(__name__)


class IngestionResult:
    """Result of ingestion operation."""
    
    def __init__(self):
        self.transactions: List[Transaction] = []
        self.errors: List[Dict] = []
        self.warnings: List[Dict] = []
        self.stats: Dict = {}
    
    def to_dict(self) -> dict:
        return {
            "transactions_count": len(self.transactions),
            "errors_count": len(self.errors),
            "warnings_count": len(self.warnings),
            "stats": self.stats,
            "errors": self.errors,
            "warnings": self.warnings
        }


class IngestionService:
    """Main service for ingesting financial data."""
    
    def __init__(self, strict_validation: bool = False):
        """
        Initialize ingestion service.
        
        Args:
            strict_validation: If True, reject transactions with warnings
        """
        self.strict_validation = strict_validation
        self.validator = TransactionValidator(strict=strict_validation)
    
    def ingest_bank_statement(
        self,
        filepath: str,
        column_mapping: Optional[ColumnMapping] = None
    ) -> IngestionResult:
        """
        Ingest a bank statement CSV file.
        
        Args:
            filepath: Path to bank statement CSV
            column_mapping: Optional column mapping (auto-detected if not provided)
        
        Returns:
            IngestionResult with transactions and validation info
        """
        logger.info(f"Ingesting bank statement from {filepath}")
        
        result = IngestionResult()
        
        try:
            parser = BankStatementParser(column_mapping=column_mapping)
            transactions = parser.parse_file(filepath)
            
            # Validate transactions
            for tx in transactions:
                validation_errors = self.validator.validate(tx)
                
                has_errors = any(e.severity == "error" for e in validation_errors)
                has_warnings = any(e.severity == "warning" for e in validation_errors)
                
                if has_errors or (self.strict_validation and has_warnings):
                    # Log and skip invalid transactions
                    for error in validation_errors:
                        if error.severity == "error":
                            result.errors.append({
                                "transaction_id": tx.id,
                                "row": tx.source_row,
                                "error": error.to_dict()
                            })
                        else:
                            result.warnings.append({
                                "transaction_id": tx.id,
                                "row": tx.source_row,
                                "warning": error.to_dict()
                            })
                else:
                    # Add warnings but include transaction
                    for error in validation_errors:
                        if error.severity == "warning":
                            result.warnings.append({
                                "transaction_id": tx.id,
                                "row": tx.source_row,
                                "warning": error.to_dict()
                            })
                    
                    result.transactions.append(tx)
            
            # Calculate statistics
            result.stats = self._calculate_stats(transactions, result)
            
            logger.info(
                f"Ingested {len(result.transactions)} transactions from bank statement "
                f"({len(result.errors)} errors, {len(result.warnings)} warnings)"
            )
        
        except Exception as e:
            logger.error(f"Error ingesting bank statement: {e}", exc_info=True)
            result.errors.append({
                "file": filepath,
                "error": {"message": str(e), "severity": "error"}
            })
        
        return result
    
    def ingest_ledger(
        self,
        filepath: str,
        column_mapping: Optional[ColumnMapping] = None
    ) -> IngestionResult:
        """
        Ingest an internal ledger CSV file.
        
        Args:
            filepath: Path to ledger CSV
            column_mapping: Optional column mapping (auto-detected if not provided)
        
        Returns:
            IngestionResult with transactions and validation info
        """
        logger.info(f"Ingesting ledger from {filepath}")
        
        result = IngestionResult()
        
        try:
            parser = LedgerParser(column_mapping=column_mapping)
            transactions = parser.parse_file(filepath)
            
            # Validate transactions
            for tx in transactions:
                validation_errors = self.validator.validate(tx)
                
                has_errors = any(e.severity == "error" for e in validation_errors)
                has_warnings = any(e.severity == "warning" for e in validation_errors)
                
                if has_errors or (self.strict_validation and has_warnings):
                    # Log and skip invalid transactions
                    for error in validation_errors:
                        if error.severity == "error":
                            result.errors.append({
                                "transaction_id": tx.id,
                                "row": tx.source_row,
                                "error": error.to_dict()
                            })
                        else:
                            result.warnings.append({
                                "transaction_id": tx.id,
                                "row": tx.source_row,
                                "warning": error.to_dict()
                            })
                else:
                    # Add warnings but include transaction
                    for error in validation_errors:
                        if error.severity == "warning":
                            result.warnings.append({
                                "transaction_id": tx.id,
                                "row": tx.source_row,
                                "warning": error.to_dict()
                            })
                    
                    result.transactions.append(tx)
            
            # Calculate statistics
            result.stats = self._calculate_stats(transactions, result)
            
            logger.info(
                f"Ingested {len(result.transactions)} transactions from ledger "
                f"({len(result.errors)} errors, {len(result.warnings)} warnings)"
            )
        
        except Exception as e:
            logger.error(f"Error ingesting ledger: {e}", exc_info=True)
            result.errors.append({
                "file": filepath,
                "error": {"message": str(e), "severity": "error"}
            })
        
        return result
    
    def _calculate_stats(self, transactions: List[Transaction], result: IngestionResult) -> Dict:
        """Calculate ingestion statistics."""
        if not transactions:
            return {
                "total_parsed": 0,
                "total_valid": 0,
                "total_invalid": 0,
                "date_range": None,
                "amount_range": None,
                "total_debits": 0,
                "total_credits": 0
            }
        
        dates = [tx.date for tx in transactions if tx.date]
        amounts = [tx.amount for tx in transactions if tx.amount]
        
        debits = [tx for tx in transactions if tx.transaction_type.value == "debit"]
        credits = [tx for tx in transactions if tx.transaction_type.value == "credit"]
        
        return {
            "total_parsed": len(transactions),
            "total_valid": len(result.transactions),
            "total_invalid": len(result.errors),
            "date_range": {
                "min": min(dates).isoformat() if dates else None,
                "max": max(dates).isoformat() if dates else None
            },
            "amount_range": {
                "min": str(min(amounts)) if amounts else None,
                "max": str(max(amounts)) if amounts else None
            },
            "total_debits": len(debits),
            "total_credits": len(credits),
            "total_debit_amount": str(sum(tx.amount for tx in debits)),
            "total_credit_amount": str(sum(tx.amount for tx in credits))
        }

