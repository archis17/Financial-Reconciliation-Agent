"""
Database session management with async support.
"""

import os
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import NullPool
import logging

logger = logging.getLogger(__name__)

# Get database URL from environment
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://user:password@localhost/dbname"
)

# Convert postgresql:// to postgresql+asyncpg:// if needed
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

# Handle SSL parameters for asyncpg
# asyncpg doesn't support sslmode/channel_binding in URL, so we remove them
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
parsed = urlparse(DATABASE_URL)
query_params = parse_qs(parsed.query)
ssl_mode = query_params.pop('sslmode', None)
channel_binding = query_params.pop('channel_binding', None)

# Reconstruct URL without sslmode/channel_binding
new_query = urlencode(query_params, doseq=True)
DATABASE_URL = urlunparse((
    parsed.scheme,
    parsed.netloc,
    parsed.path,
    parsed.params,
    new_query,
    parsed.fragment
))

# Determine if SSL is required
SSL_REQUIRED = ssl_mode and ssl_mode[0] == 'require'

# Pool configuration
POOL_SIZE = int(os.getenv("DATABASE_POOL_SIZE", "10"))
MAX_OVERFLOW = int(os.getenv("DATABASE_MAX_OVERFLOW", "20"))

# Configure SSL for asyncpg if required
connect_args = {}
if SSL_REQUIRED:
    import ssl
    connect_args['ssl'] = ssl.create_default_context()

# Create async engine
engine = create_async_engine(
    DATABASE_URL,
    pool_size=POOL_SIZE,
    max_overflow=MAX_OVERFLOW,
    pool_pre_ping=True,  # Verify connections before using
    echo=os.getenv("DATABASE_ECHO", "false").lower() == "true",
    connect_args=connect_args,
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Base class for models
Base = declarative_base()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for getting database session.
    
    Yields:
        AsyncSession: Database session
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """
    Initialize database - create all tables.
    """
    try:
        async with engine.begin() as conn:
            # Import all models to ensure they're registered
            from .models import User, Reconciliation, ReconciliationResult, AuditLog
            
            # Create all tables
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {e}", exc_info=True)
        raise


async def close_db() -> None:
    """
    Close database connections.
    """
    await engine.dispose()
    logger.info("Database connections closed")

