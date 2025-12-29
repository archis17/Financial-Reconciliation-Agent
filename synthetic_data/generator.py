"""
Main synthetic data generator.
"""

from dataclasses import dataclass
from decimal import Decimal
from datetime import date, timedelta
from typing import List, Optional
import uuid
import random

from .transaction_templates import (
    get_random_template,
    generate_description,
    generate_amount,
    should_generate_transaction
)
from .noise_injector import NoiseInjector, NoiseConfig
from .ground_truth import GroundTruthManager, GroundTruthEntry
from .csv_formatter import BankStatementFormatter, LedgerFormatter, TransactionRow


@dataclass
class GeneratorConfig:
    """Configuration for synthetic data generation."""
    num_transactions: int = 100
    date_range_start: date = date(2024, 1, 1)
    date_range_end: date = date(2024, 1, 31)
    
    # Match rate controls (should sum to <= 1.0)
    perfect_match_rate: float = 0.7  # 70% perfect matches
    fuzzy_match_rate: float = 0.2     # 20% fuzzy matches
    missing_in_bank_rate: float = 0.05  # 5% missing in bank
    missing_in_ledger_rate: float = 0.05  # 5% missing in ledger
    
    # Noise parameters
    date_drift_max_days: int = 7
    amount_tolerance_max: Decimal = Decimal("5.00")
    description_variation_rate: float = 0.3
    
    # Transaction type distribution
    debit_percentage: float = 0.6  # 60% debits, 40% credits


class SyntheticDataGenerator:
    """Generates synthetic bank statements and ledger data."""
    
    def __init__(self, config: GeneratorConfig):
        self.config = config
        self.noise_config = NoiseConfig(
            date_drift_max_days=config.date_drift_max_days,
            amount_tolerance_max=config.amount_tolerance_max,
            description_variation_rate=config.description_variation_rate,
            missing_rate=0.0  # Controlled separately
        )
        self.noise_injector = NoiseInjector(self.noise_config)
        self.ground_truth = GroundTruthManager()
    
    def generate(self) -> dict:
        """
        Generate synthetic data.
        
        Returns:
            Dictionary with paths to generated files and ground truth
        """
        # Generate ground truth transactions
        true_transactions = self._generate_true_transactions()
        
        # Create bank and ledger representations with noise
        bank_transactions = []
        ledger_transactions = []
        
        for true_tx in true_transactions:
            # Determine match type
            match_type = self._determine_match_type()
            
            # Generate bank representation
            if match_type != "missing_in_bank":
                bank_noise = self._apply_noise_for_match_type(
                    true_tx, match_type, "bank"
                )
                if bank_noise.present:
                    bank_transactions.append(self._create_bank_row(
                        true_tx, bank_noise
                    ))
                    true_tx.bank_present = True
                    true_tx.bank_date = bank_noise.date
                    true_tx.bank_amount = bank_noise.amount
                    true_tx.bank_description = bank_noise.description
                else:
                    true_tx.bank_present = False
            else:
                true_tx.bank_present = False
            
            # Generate ledger representation
            if match_type != "missing_in_ledger":
                ledger_noise = self._apply_noise_for_match_type(
                    true_tx, match_type, "ledger"
                )
                if ledger_noise.present:
                    ledger_transactions.append(self._create_ledger_row(
                        true_tx, ledger_noise
                    ))
                    true_tx.ledger_present = True
                    true_tx.ledger_date = ledger_noise.date
                    true_tx.ledger_amount = ledger_noise.amount
                    true_tx.ledger_description = ledger_noise.description
                else:
                    true_tx.ledger_present = False
            else:
                true_tx.ledger_present = False
            
            # Add to ground truth
            self.ground_truth.add_entry(true_tx)
        
        # Sort transactions by date
        bank_transactions.sort(key=lambda x: x.date)
        ledger_transactions.sort(key=lambda x: x.date)
        
        return {
            "bank_transactions": bank_transactions,
            "ledger_transactions": ledger_transactions,
            "ground_truth": self.ground_truth
        }
    
    def _generate_true_transactions(self) -> List[GroundTruthEntry]:
        """Generate the true transactions (ground truth)."""
        transactions = []
        date_range = (self.config.date_range_end - self.config.date_range_start).days
        
        for i in range(self.config.num_transactions):
            # Random date in range
            days_offset = random.randint(0, date_range)
            tx_date = self.config.date_range_start + timedelta(days=days_offset)
            
            # Get template and generate transaction
            template = get_random_template()
            
            # Override transaction type based on config
            tx_type = "debit" if random.random() < self.config.debit_percentage else "credit"
            if template.transaction_type != tx_type:
                # Find a template matching the desired type
                from .transaction_templates import MERCHANT_TEMPLATES
                matching_templates = [t for t in MERCHANT_TEMPLATES if t.transaction_type == tx_type]
                if matching_templates:
                    template = random.choice(matching_templates)
            
            amount = generate_amount(template)
            description = generate_description(template, variation_level="none")
            
            # Generate reference
            reference = f"REF{random.randint(100000, 999999)}"
            
            entry = GroundTruthEntry(
                transaction_id=str(uuid.uuid4()),
                true_date=tx_date,
                true_amount=amount,
                transaction_type=tx_type,
                true_description=description,
                noise_applied={}
            )
            
            transactions.append(entry)
        
        return transactions
    
    def _determine_match_type(self) -> str:
        """
        Determine the match type for a transaction.
        
        Returns:
            "perfect", "fuzzy", "missing_in_bank", or "missing_in_ledger"
        """
        rand = random.random()
        cumulative = 0.0
        
        cumulative += self.config.perfect_match_rate
        if rand < cumulative:
            return "perfect"
        
        cumulative += self.config.fuzzy_match_rate
        if rand < cumulative:
            return "fuzzy"
        
        cumulative += self.config.missing_in_bank_rate
        if rand < cumulative:
            return "missing_in_bank"
        
        cumulative += self.config.missing_in_ledger_rate
        if rand < cumulative:
            return "missing_in_ledger"
        
        # Default to perfect if rates don't sum to 1.0
        return "perfect"
    
    def _apply_noise_for_match_type(
        self,
        true_tx: GroundTruthEntry,
        match_type: str,
        source: str
    ):
        """Apply noise based on match type."""
        if match_type == "perfect":
            # Minimal or no noise
            variation_level = "none"
            # Temporarily set missing_rate to 0
            original_missing = self.noise_config.missing_rate
            self.noise_config.missing_rate = 0.0
            self.noise_injector.config.missing_rate = 0.0
            
            result = self.noise_injector.inject_noise(
                true_tx.true_date,
                true_tx.true_amount,
                true_tx.true_description,
                variation_level
            )
            
            self.noise_config.missing_rate = original_missing
            self.noise_injector.config.missing_rate = original_missing
            
            # Store noise metadata
            true_tx.noise_applied = result.noise_applied
            
            return result
        
        elif match_type == "fuzzy":
            # Apply moderate noise
            variation_level = random.choice(["minor", "major"])
            result = self.noise_injector.inject_noise(
                true_tx.true_date,
                true_tx.true_amount,
                true_tx.true_description,
                variation_level
            )
            
            # Ensure it's present (not missing)
            result.present = True
            true_tx.noise_applied = result.noise_applied
            
            return result
        
        else:
            # Missing entry - return a result indicating absence
            return self.noise_injector.inject_noise(
                true_tx.true_date,
                true_tx.true_amount,
                true_tx.true_description,
                "none"
            )
    
    def _create_bank_row(
        self,
        true_tx: GroundTruthEntry,
        noise_result
    ) -> TransactionRow:
        """Create a bank statement row."""
        return TransactionRow(
            date=noise_result.date,
            description=noise_result.description,
            amount=noise_result.amount,
            transaction_type=true_tx.transaction_type,
            reference=f"BANK{true_tx.transaction_id[:8].upper()}"
        )
    
    def _create_ledger_row(
        self,
        true_tx: GroundTruthEntry,
        noise_result
    ) -> TransactionRow:
        """Create a ledger row."""
        # Determine account based on category
        account = "Expenses" if true_tx.transaction_type == "debit" else "Income"
        
        return TransactionRow(
            date=noise_result.date,
            description=noise_result.description,
            amount=noise_result.amount,
            transaction_type=true_tx.transaction_type,
            reference=f"LEDGER{true_tx.transaction_id[:8].upper()}",
            account=account,
            posting_date=noise_result.date  # Same as transaction date for simplicity
        )
    
    def save_outputs(self, output_dir: str = "test_data") -> dict:
        """
        Generate and save all outputs.
        
        Returns:
            Dictionary with file paths
        """
        import os
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate data
        result = self.generate()
        
        # Save bank statement
        bank_path = os.path.join(output_dir, "bank_statement.csv")
        BankStatementFormatter.save(result["bank_transactions"], bank_path)
        
        # Save ledger
        ledger_path = os.path.join(output_dir, "internal_ledger.csv")
        LedgerFormatter.save(result["ledger_transactions"], ledger_path)
        
        # Save ground truth
        gt_path = os.path.join(output_dir, "ground_truth.json")
        result["ground_truth"].save(gt_path)
        
        # Save summary
        summary_path = os.path.join(output_dir, "ground_truth_summary.json")
        import json
        with open(summary_path, 'w') as f:
            json.dump(result["ground_truth"].get_statistics(), f, indent=2, default=str)
        
        return {
            "bank_statement": bank_path,
            "internal_ledger": ledger_path,
            "ground_truth": gt_path,
            "summary": summary_path
        }

