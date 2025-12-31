#!/usr/bin/env python3
"""Quick script to check database records."""
import asyncio
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.session import AsyncSessionLocal
from database.repository import ReconciliationRepository, ReconciliationResultRepository, UserRepository


async def check_database():
    from sqlalchemy import select, func
    from database.models import User, Reconciliation, ReconciliationResult
    
    async with AsyncSessionLocal() as db:
        # Count users
        user_result = await db.execute(select(func.count(User.id)))
        user_count = user_result.scalar() or 0
        
        # Count reconciliations
        recon_result = await db.execute(select(func.count(Reconciliation.id)))
        reconciliation_count = recon_result.scalar() or 0
        
        # Count results
        result_query = await db.execute(select(func.count(ReconciliationResult.id)))
        result_count = result_query.scalar() or 0
        
        print(f"Users in database: {user_count}")
        print(f"Reconciliations in database: {reconciliation_count}")
        print(f"Reconciliation results in database: {result_count}")
        
        if reconciliation_count > 0:
            # Get latest reconciliation
            latest_query = await db.execute(
                select(Reconciliation)
                .order_by(Reconciliation.created_at.desc())
                .limit(1)
            )
            latest = latest_query.scalar_one_or_none()
            if latest:
                print(f"\nLatest reconciliation:")
                print(f"  ID: {latest.id}")
                print(f"  Status: {latest.status}")
                print(f"  Created: {latest.created_at}")
                print(f"  User ID: {latest.user_id}")
                if latest.bank_file_path:
                    print(f"  Bank file: {latest.bank_file_path}")
                if latest.ledger_file_path:
                    print(f"  Ledger file: {latest.ledger_file_path}")


if __name__ == "__main__":
    asyncio.run(check_database())

