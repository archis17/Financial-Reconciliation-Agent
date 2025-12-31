"""
SQLAlchemy models for the database.
"""

from datetime import datetime
from typing import Optional
import json

from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, Text, Float, JSON
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import os

from .session import Base, IS_SQLITE

# Use database-agnostic types
# For PostgreSQL, use native UUID and JSONB
# For SQLite, use String for UUID and JSON for JSONB
if IS_SQLITE:
    # SQLite doesn't support UUID natively, use String
    UUID = String(36)  # UUID as string
    JSON_TYPE = JSON  # SQLite 3.9+ supports JSON
    
    def uuid_default():
        return str(uuid.uuid4())
else:
    # PostgreSQL supports native UUID and JSONB
    UUID = PostgresUUID(as_uuid=True)
    JSON_TYPE = JSONB
    
    def uuid_default():
        return uuid.uuid4()


class User(Base):
    """User model for authentication."""
    
    __tablename__ = "users"
    
    id = Column(UUID, primary_key=True, default=uuid_default)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    reconciliations = relationship("Reconciliation", back_populates="user", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(id={self.id}, email={self.email})>"


class Reconciliation(Base):
    """Reconciliation run model."""
    
    __tablename__ = "reconciliations"
    
    id = Column(UUID, primary_key=True, default=uuid_default)
    user_id = Column(UUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String(50), nullable=False, default="pending", index=True)  # pending, processing, completed, failed
    bank_file_path = Column(String(500), nullable=True)
    ledger_file_path = Column(String(500), nullable=True)
    config_json = Column(JSON_TYPE, nullable=True)  # Store reconciliation config as JSON
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="reconciliations")
    result = relationship("ReconciliationResult", back_populates="reconciliation", uselist=False, cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Reconciliation(id={self.id}, user_id={self.user_id}, status={self.status})>"


class ReconciliationResult(Base):
    """Reconciliation result data model."""
    
    __tablename__ = "reconciliation_results"
    
    id = Column(UUID, primary_key=True, default=uuid_default)
    reconciliation_id = Column(UUID, ForeignKey("reconciliations.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    report_json = Column(JSON_TYPE, nullable=False)  # ReconciliationReport as JSON
    match_result_json = Column(JSON_TYPE, nullable=True)  # MatchResult as JSON
    discrepancy_result_json = Column(JSON_TYPE, nullable=True)  # DiscrepancyResult as JSON
    tickets_json = Column(JSON_TYPE, nullable=True)  # List of tickets as JSON
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    reconciliation = relationship("Reconciliation", back_populates="result")
    
    def __repr__(self):
        return f"<ReconciliationResult(id={self.id}, reconciliation_id={self.reconciliation_id})>"


class AuditLog(Base):
    """Audit log for tracking user actions."""
    
    __tablename__ = "audit_logs"
    
    id = Column(UUID, primary_key=True, default=uuid_default)
    user_id = Column(UUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)  # Nullable for system actions
    action = Column(String(100), nullable=False, index=True)  # e.g., "reconciliation_created", "user_login", "file_uploaded"
    resource_type = Column(String(100), nullable=True)  # e.g., "reconciliation", "user", "file"
    resource_id = Column(String(255), nullable=True)  # ID of the resource
    metadata_json = Column(JSON_TYPE, nullable=True)  # Additional metadata as JSON
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    
    # Relationships
    user = relationship("User", back_populates="audit_logs")
    
    def __repr__(self):
        return f"<AuditLog(id={self.id}, user_id={self.user_id}, action={self.action})>"

