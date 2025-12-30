"""
Repository pattern for database operations.
"""

from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func, and_
from sqlalchemy.orm import selectinload

from .models import User, Reconciliation, ReconciliationResult, AuditLog


class UserRepository:
    """Repository for user operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(self, email: str, hashed_password: str) -> User:
        """Create a new user."""
        user = User(email=email, hashed_password=hashed_password)
        self.session.add(user)
        await self.session.flush()
        return user
    
    async def get_by_id(self, user_id: UUID) -> Optional[User]:
        """Get user by ID."""
        result = await self.session.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        result = await self.session.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()
    
    async def update(self, user: User) -> User:
        """Update user."""
        user.updated_at = datetime.utcnow()
        await self.session.flush()
        return user


class ReconciliationRepository:
    """Repository for reconciliation operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(
        self,
        user_id: UUID,
        bank_file_path: Optional[str] = None,
        ledger_file_path: Optional[str] = None,
        config_json: Optional[Dict[str, Any]] = None,
        status: str = "pending"
    ) -> Reconciliation:
        """Create a new reconciliation."""
        reconciliation = Reconciliation(
            user_id=user_id,
            bank_file_path=bank_file_path,
            ledger_file_path=ledger_file_path,
            config_json=config_json,
            status=status
        )
        self.session.add(reconciliation)
        await self.session.flush()
        return reconciliation
    
    async def get_by_id(self, reconciliation_id: UUID, user_id: Optional[UUID] = None) -> Optional[Reconciliation]:
        """Get reconciliation by ID, optionally scoped to user."""
        query = select(Reconciliation).where(Reconciliation.id == reconciliation_id)
        if user_id:
            query = query.where(Reconciliation.user_id == user_id)
        
        result = await self.session.execute(query.options(selectinload(Reconciliation.result)))
        return result.scalar_one_or_none()
    
    async def get_by_user(
        self,
        user_id: UUID,
        limit: int = 100,
        offset: int = 0,
        status: Optional[str] = None
    ) -> List[Reconciliation]:
        """Get reconciliations for a user."""
        query = select(Reconciliation).where(Reconciliation.user_id == user_id)
        if status:
            query = query.where(Reconciliation.status == status)
        
        query = query.order_by(Reconciliation.created_at.desc()).limit(limit).offset(offset)
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def update_status(self, reconciliation_id: UUID, status: str, completed_at: Optional[datetime] = None) -> bool:
        """Update reconciliation status."""
        update_data = {"status": status}
        if completed_at:
            update_data["completed_at"] = completed_at
        
        result = await self.session.execute(
            update(Reconciliation)
            .where(Reconciliation.id == reconciliation_id)
            .values(**update_data)
        )
        await self.session.flush()
        return result.rowcount > 0
    
    async def delete(self, reconciliation_id: UUID, user_id: UUID) -> bool:
        """Delete reconciliation (user-scoped)."""
        result = await self.session.execute(
            delete(Reconciliation).where(
                and_(
                    Reconciliation.id == reconciliation_id,
                    Reconciliation.user_id == user_id
                )
            )
        )
        await self.session.flush()
        return result.rowcount > 0


class ReconciliationResultRepository:
    """Repository for reconciliation result operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(
        self,
        reconciliation_id: UUID,
        report_json: Dict[str, Any],
        match_result_json: Optional[Dict[str, Any]] = None,
        discrepancy_result_json: Optional[Dict[str, Any]] = None,
        tickets_json: Optional[List[Dict[str, Any]]] = None
    ) -> ReconciliationResult:
        """Create reconciliation result."""
        result = ReconciliationResult(
            reconciliation_id=reconciliation_id,
            report_json=report_json,
            match_result_json=match_result_json,
            discrepancy_result_json=discrepancy_result_json,
            tickets_json=tickets_json
        )
        self.session.add(result)
        await self.session.flush()
        return result
    
    async def get_by_reconciliation_id(self, reconciliation_id: UUID) -> Optional[ReconciliationResult]:
        """Get result by reconciliation ID."""
        result = await self.session.execute(
            select(ReconciliationResult).where(
                ReconciliationResult.reconciliation_id == reconciliation_id
            )
        )
        return result.scalar_one_or_none()
    
    async def update(
        self,
        reconciliation_id: UUID,
        report_json: Optional[Dict[str, Any]] = None,
        match_result_json: Optional[Dict[str, Any]] = None,
        discrepancy_result_json: Optional[Dict[str, Any]] = None,
        tickets_json: Optional[List[Dict[str, Any]]] = None
    ) -> bool:
        """Update reconciliation result."""
        update_data = {}
        if report_json is not None:
            update_data["report_json"] = report_json
        if match_result_json is not None:
            update_data["match_result_json"] = match_result_json
        if discrepancy_result_json is not None:
            update_data["discrepancy_result_json"] = discrepancy_result_json
        if tickets_json is not None:
            update_data["tickets_json"] = tickets_json
        
        if not update_data:
            return False
        
        result = await self.session.execute(
            update(ReconciliationResult)
            .where(ReconciliationResult.reconciliation_id == reconciliation_id)
            .values(**update_data)
        )
        await self.session.flush()
        return result.rowcount > 0


class AuditLogRepository:
    """Repository for audit log operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(
        self,
        action: str,
        user_id: Optional[UUID] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        metadata_json: Optional[Dict[str, Any]] = None
    ) -> AuditLog:
        """Create audit log entry."""
        log = AuditLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            metadata_json=metadata_json
        )
        self.session.add(log)
        await self.session.flush()
        return log
    
    async def get_by_user(
        self,
        user_id: UUID,
        limit: int = 100,
        offset: int = 0
    ) -> List[AuditLog]:
        """Get audit logs for a user."""
        result = await self.session.execute(
            select(AuditLog)
            .where(AuditLog.user_id == user_id)
            .order_by(AuditLog.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())
    
    async def get_by_action(
        self,
        action: str,
        limit: int = 100,
        offset: int = 0
    ) -> List[AuditLog]:
        """Get audit logs by action."""
        result = await self.session.execute(
            select(AuditLog)
            .where(AuditLog.action == action)
            .order_by(AuditLog.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

