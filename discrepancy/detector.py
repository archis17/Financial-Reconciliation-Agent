"""
Main discrepancy detection logic.
"""

import logging
from typing import List, Dict, Set
from decimal import Decimal
from collections import defaultdict

from ingestion.models import Transaction
from matching.models import Match, MatchResult
from discrepancy.models import Discrepancy, DiscrepancyType, DiscrepancySeverity, DiscrepancyResult
from discrepancy.classifier import DiscrepancyClassifier

logger = logging.getLogger(__name__)


class DiscrepancyDetector:
    """Detects and classifies discrepancies."""
    
    def __init__(
        self,
        classifier: DiscrepancyClassifier = None
    ):
        """
        Initialize discrepancy detector.
        
        Args:
            classifier: Discrepancy classifier (default: standard classifier)
        """
        self.classifier = classifier or DiscrepancyClassifier()
    
    def detect(
        self,
        bank_transactions: List[Transaction],
        ledger_transactions: List[Transaction],
        match_result: MatchResult
    ) -> DiscrepancyResult:
        """
        Detect discrepancies from matching results.
        
        Args:
            bank_transactions: All bank transactions
            ledger_transactions: All ledger transactions
            match_result: Result from matching engine
        
        Returns:
            DiscrepancyResult with all detected discrepancies
        """
        logger.info("Detecting discrepancies...")
        
        discrepancies: List[Discrepancy] = []
        
        # Create lookup dictionaries
        bank_tx_dict = {tx.id: tx for tx in bank_transactions}
        ledger_tx_dict = {tx.id: tx for tx in ledger_transactions}
        match_dict = {m.bank_transaction_id: m for m in match_result.matches}
        
        # 1. Detect missing transactions
        missing_discrepancies = self._detect_missing(
            match_result.unmatched_bank,
            match_result.unmatched_ledger,
            bank_tx_dict,
            ledger_tx_dict
        )
        discrepancies.extend(missing_discrepancies)
        
        # 2. Detect amount mismatches in matches
        amount_mismatches = self._detect_amount_mismatches(
            match_result.matches,
            bank_tx_dict,
            ledger_tx_dict
        )
        discrepancies.extend(amount_mismatches)
        
        # 3. Detect date mismatches in matches
        date_mismatches = self._detect_date_mismatches(
            match_result.matches,
            bank_tx_dict,
            ledger_tx_dict
        )
        discrepancies.extend(date_mismatches)
        
        # 4. Detect duplicates
        duplicates = self._detect_duplicates(
            bank_transactions,
            ledger_transactions
        )
        discrepancies.extend(duplicates)
        
        # 5. Detect suspicious patterns
        suspicious = self._detect_suspicious(
            bank_transactions,
            ledger_transactions
        )
        discrepancies.extend(suspicious)
        
        # Create result and calculate summary
        result = DiscrepancyResult(discrepancies=discrepancies)
        self._calculate_summary(result)
        
        logger.info(
            f"Detected {len(discrepancies)} discrepancies "
            f"({result.critical_count} critical, {result.high_count} high)"
        )
        
        return result
    
    def _detect_missing(
        self,
        unmatched_bank_ids: List[str],
        unmatched_ledger_ids: List[str],
        bank_tx_dict: Dict[str, Transaction],
        ledger_tx_dict: Dict[str, Transaction]
    ) -> List[Discrepancy]:
        """Detect missing transactions."""
        discrepancies = []
        
        # Missing in ledger
        for tx_id in unmatched_bank_ids:
            tx = bank_tx_dict.get(tx_id)
            if tx:
                disc_type, severity, reason = self.classifier.classify_missing(tx)
                
                discrepancy = Discrepancy(
                    transaction_id=tx_id,
                    source="bank",
                    discrepancy_type=disc_type,
                    severity=severity,
                    machine_reason=reason,
                    amount=tx.amount,
                    date=tx.date,
                    description=tx.description,
                    suggested_action="Verify transaction was recorded in ledger"
                )
                discrepancies.append(discrepancy)
        
        # Missing in bank
        for tx_id in unmatched_ledger_ids:
            tx = ledger_tx_dict.get(tx_id)
            if tx:
                disc_type, severity, reason = self.classifier.classify_missing(tx)
                
                discrepancy = Discrepancy(
                    transaction_id=tx_id,
                    source="ledger",
                    discrepancy_type=disc_type,
                    severity=severity,
                    machine_reason=reason,
                    amount=tx.amount,
                    date=tx.date,
                    description=tx.description,
                    suggested_action="Verify transaction appears in bank statement"
                )
                discrepancies.append(discrepancy)
        
        return discrepancies
    
    def _detect_amount_mismatches(
        self,
        matches: List[Match],
        bank_tx_dict: Dict[str, Transaction],
        ledger_tx_dict: Dict[str, Transaction]
    ) -> List[Discrepancy]:
        """Detect amount mismatches in matched transactions."""
        discrepancies = []
        
        for match in matches:
            bank_tx = bank_tx_dict.get(match.bank_transaction_id)
            ledger_tx = ledger_tx_dict.get(match.ledger_transaction_id)
            
            if not bank_tx or not ledger_tx:
                continue
            
            # Check if amount difference is significant
            amount_diff = abs(match.amount_difference)
            if amount_diff > self.classifier.amount_tolerance:
                severity, reason = self.classifier.classify_amount_mismatch(
                    match, bank_tx, ledger_tx
                )
                
                discrepancy = Discrepancy(
                    transaction_id=match.bank_transaction_id,
                    source="bank",
                    discrepancy_type=DiscrepancyType.AMOUNT_MISMATCH,
                    severity=severity,
                    machine_reason=reason,
                    related_transaction_id=match.ledger_transaction_id,
                    amount=bank_tx.amount,
                    date=bank_tx.date,
                    description=bank_tx.description,
                    expected_amount=ledger_tx.amount,
                    actual_amount=bank_tx.amount,
                    amount_difference=amount_diff,
                    suggested_action="Investigate amount difference - may be fees or errors"
                )
                discrepancies.append(discrepancy)
        
        return discrepancies
    
    def _detect_date_mismatches(
        self,
        matches: List[Match],
        bank_tx_dict: Dict[str, Transaction],
        ledger_tx_dict: Dict[str, Transaction]
    ) -> List[Discrepancy]:
        """Detect date mismatches in matched transactions."""
        discrepancies = []
        
        for match in matches:
            bank_tx = bank_tx_dict.get(match.bank_transaction_id)
            ledger_tx = ledger_tx_dict.get(match.ledger_transaction_id)
            
            if not bank_tx or not ledger_tx:
                continue
            
            # Check if date difference is significant
            date_diff = abs(match.date_difference_days)
            if date_diff > self.classifier.date_window_days:
                severity, reason = self.classifier.classify_date_mismatch(
                    match, bank_tx, ledger_tx
                )
                
                discrepancy = Discrepancy(
                    transaction_id=match.bank_transaction_id,
                    source="bank",
                    discrepancy_type=DiscrepancyType.DATE_MISMATCH,
                    severity=severity,
                    machine_reason=reason,
                    related_transaction_id=match.ledger_transaction_id,
                    amount=bank_tx.amount,
                    date=bank_tx.date,
                    description=bank_tx.description,
                    expected_date=ledger_tx.date,
                    actual_date=bank_tx.date,
                    date_difference_days=date_diff,
                    suggested_action="Verify posting dates - may be timing difference"
                )
                discrepancies.append(discrepancy)
        
        return discrepancies
    
    def _detect_duplicates(
        self,
        bank_transactions: List[Transaction],
        ledger_transactions: List[Transaction]
    ) -> List[Discrepancy]:
        """Detect duplicate transactions."""
        discrepancies = []
        
        # Group transactions by key (amount, date, description)
        def get_key(tx: Transaction) -> tuple:
            return (
                tx.amount,
                tx.date,
                tx.description.upper().strip()[:50]  # First 50 chars
            )
        
        # Check bank transactions
        bank_groups = defaultdict(list)
        for tx in bank_transactions:
            bank_groups[get_key(tx)].append(tx)
        
        for key, txs in bank_groups.items():
            if len(txs) > 1:
                severity, reason = self.classifier.classify_duplicate(txs)
                
                # Create discrepancy for each duplicate (after first)
                for tx in txs[1:]:
                    discrepancy = Discrepancy(
                        transaction_id=tx.id,
                        source="bank",
                        discrepancy_type=DiscrepancyType.DUPLICATE,
                        severity=severity,
                        machine_reason=f"{reason} - Bank statement",
                        amount=tx.amount,
                        date=tx.date,
                        description=tx.description,
                        related_transaction_id=txs[0].id,
                        suggested_action="Remove duplicate entry"
                    )
                    discrepancies.append(discrepancy)
        
        # Check ledger transactions
        ledger_groups = defaultdict(list)
        for tx in ledger_transactions:
            ledger_groups[get_key(tx)].append(tx)
        
        for key, txs in ledger_groups.items():
            if len(txs) > 1:
                severity, reason = self.classifier.classify_duplicate(txs)
                
                # Create discrepancy for each duplicate (after first)
                for tx in txs[1:]:
                    discrepancy = Discrepancy(
                        transaction_id=tx.id,
                        source="ledger",
                        discrepancy_type=DiscrepancyType.DUPLICATE,
                        severity=severity,
                        machine_reason=f"{reason} - Ledger",
                        amount=tx.amount,
                        date=tx.date,
                        description=tx.description,
                        related_transaction_id=txs[0].id,
                        suggested_action="Remove duplicate entry"
                    )
                    discrepancies.append(discrepancy)
        
        return discrepancies
    
    def _detect_suspicious(
        self,
        bank_transactions: List[Transaction],
        ledger_transactions: List[Transaction]
    ) -> List[Discrepancy]:
        """Detect suspicious/fraud patterns."""
        discrepancies = []
        
        # Check all transactions for suspicious patterns
        for tx in bank_transactions + ledger_transactions:
            severity, reason = self.classifier.classify_suspicious(tx)
            
            if severity and reason:
                discrepancy = Discrepancy(
                    transaction_id=tx.id,
                    source=tx.source.value,
                    discrepancy_type=DiscrepancyType.POSSIBLE_FRAUD,
                    severity=severity,
                    machine_reason=reason,
                    amount=tx.amount,
                    date=tx.date,
                    description=tx.description,
                    suggested_action="Review transaction for potential fraud or error"
                )
                discrepancies.append(discrepancy)
        
        return discrepancies
    
    def _calculate_summary(self, result: DiscrepancyResult):
        """Calculate summary statistics."""
        for disc in result.discrepancies:
            # Count by type
            if disc.discrepancy_type == DiscrepancyType.MISSING_IN_LEDGER:
                result.missing_in_ledger_count += 1
            elif disc.discrepancy_type == DiscrepancyType.MISSING_IN_BANK:
                result.missing_in_bank_count += 1
            elif disc.discrepancy_type == DiscrepancyType.AMOUNT_MISMATCH:
                result.amount_mismatch_count += 1
            elif disc.discrepancy_type == DiscrepancyType.DATE_MISMATCH:
                result.date_mismatch_count += 1
            elif disc.discrepancy_type == DiscrepancyType.DUPLICATE:
                result.duplicate_count += 1
            elif disc.discrepancy_type == DiscrepancyType.POSSIBLE_FRAUD:
                result.possible_fraud_count += 1
            
            # Count by severity
            if disc.severity == DiscrepancySeverity.CRITICAL:
                result.critical_count += 1
            elif disc.severity == DiscrepancySeverity.HIGH:
                result.high_count += 1
            elif disc.severity == DiscrepancySeverity.MEDIUM:
                result.medium_count += 1
            elif disc.severity == DiscrepancySeverity.LOW:
                result.low_count += 1

