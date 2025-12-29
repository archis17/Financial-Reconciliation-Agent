"""
Synthetic Test Data Generator for Financial Reconciliation System.

This module generates realistic bank statements and internal ledger data
with controlled noise injection for testing the reconciliation engine.
"""

from .generator import SyntheticDataGenerator, GeneratorConfig
from .ground_truth import GroundTruthManager

__all__ = ["SyntheticDataGenerator", "GeneratorConfig", "GroundTruthManager"]

