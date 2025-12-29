#!/usr/bin/env python3
"""
Script to generate synthetic test data for financial reconciliation.

Usage:
    python generate_test_data.py [--num-transactions N] [--output-dir DIR]
"""

import argparse
from datetime import date
from decimal import Decimal
from synthetic_data import SyntheticDataGenerator, GeneratorConfig


def main():
    parser = argparse.ArgumentParser(description="Generate synthetic test data")
    parser.add_argument(
        "--num-transactions",
        type=int,
        default=100,
        help="Number of transactions to generate (default: 100)"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="test_data",
        help="Output directory for generated files (default: test_data)"
    )
    parser.add_argument(
        "--date-start",
        type=str,
        default="2024-01-01",
        help="Start date (YYYY-MM-DD, default: 2024-01-01)"
    )
    parser.add_argument(
        "--date-end",
        type=str,
        default="2024-01-31",
        help="End date (YYYY-MM-DD, default: 2024-01-31)"
    )
    parser.add_argument(
        "--match-rate",
        type=float,
        default=0.7,
        help="Perfect match rate (0.0-1.0, default: 0.7)"
    )
    parser.add_argument(
        "--fuzzy-rate",
        type=float,
        default=0.2,
        help="Fuzzy match rate (0.0-1.0, default: 0.2)"
    )
    
    args = parser.parse_args()
    
    # Parse dates
    date_start = date.fromisoformat(args.date_start)
    date_end = date.fromisoformat(args.date_end)
    
    # Calculate missing rates to balance
    remaining = 1.0 - args.match_rate - args.fuzzy_rate
    missing_bank_rate = remaining / 2
    missing_ledger_rate = remaining / 2
    
    # Create config
    config = GeneratorConfig(
        num_transactions=args.num_transactions,
        date_range_start=date_start,
        date_range_end=date_end,
        perfect_match_rate=args.match_rate,
        fuzzy_match_rate=args.fuzzy_rate,
        missing_in_bank_rate=missing_bank_rate,
        missing_in_ledger_rate=missing_ledger_rate
    )
    
    # Generate data
    print(f"Generating {args.num_transactions} transactions...")
    print(f"Date range: {date_start} to {date_end}")
    print(f"Match rates: Perfect={args.match_rate:.1%}, Fuzzy={args.fuzzy_rate:.1%}")
    print(f"Missing rates: Bank={missing_bank_rate:.1%}, Ledger={missing_ledger_rate:.1%}")
    print()
    
    generator = SyntheticDataGenerator(config)
    files = generator.save_outputs(args.output_dir)
    
    # Print summary
    stats = generator.ground_truth.get_statistics()
    print("Generation complete!")
    print(f"\nGenerated files:")
    for key, path in files.items():
        print(f"  - {key}: {path}")
    
    print(f"\nStatistics:")
    print(f"  Total transactions: {stats['total_transactions']}")
    print(f"  Matched: {stats['matched_transactions']} ({stats['match_rate']:.1%})")
    print(f"  Missing in bank: {stats['missing_in_bank']}")
    print(f"  Missing in ledger: {stats['missing_in_ledger']}")
    
    if stats['noise_statistics']:
        noise = stats['noise_statistics']
        print(f"\nNoise statistics:")
        print(f"  Avg date drift: {noise['avg_date_drift_days']:.1f} days")
        print(f"  Max date drift: {noise['max_date_drift_days']} days")
        print(f"  Avg amount difference: ${noise['avg_amount_difference']:.2f}")
        print(f"  Max amount difference: ${noise['max_amount_difference']:.2f}")
        print(f"  Description variations: {noise['description_variations']}")


if __name__ == "__main__":
    main()

