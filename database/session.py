"""
Database session management with async support.
"""

import os
from typing import AsyncGenerator
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import NullPool
import logging

logger = logging.getLogger(__name__)

# Load .env file if it exists
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
        logger.info(f"Loaded environment variables from {env_path}")
except ImportError:
    # python-dotenv not installed, try to load .env manually
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ.setdefault(key.strip(), value.strip())
        logger.info(f"Loaded environment variables from {env_path}")

# Get database URL from environment
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite+aiosqlite:///./financial_reconciliation.db"
)

# Check if using SQLite
IS_SQLITE = DATABASE_URL.startswith("sqlite")

# Convert postgresql:// to postgresql+asyncpg:// if needed
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

# Handle SSL parameters for asyncpg (only for PostgreSQL)
# asyncpg doesn't support sslmode/channel_binding in URL, so we remove them
SSL_REQUIRED = False
if not IS_SQLITE:
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
    

# Pool configuration
# SQLite requires NullPool, PostgreSQL can use regular pool
if IS_SQLITE:
    poolclass = NullPool
    POOL_SIZE = 1
    MAX_OVERFLOW = 0
else:
    poolclass = None
    POOL_SIZE = int(os.getenv("DATABASE_POOL_SIZE", "10"))
    MAX_OVERFLOW = int(os.getenv("DATABASE_MAX_OVERFLOW", "20"))

# Configure SSL for asyncpg if required
connect_args = {}
if SSL_REQUIRED:
    import ssl
    connect_args['ssl'] = ssl.create_default_context()

# For SQLite, ensure the database directory exists
if IS_SQLITE:
    from pathlib import Path
    # Extract path from SQLite URL (sqlite+aiosqlite:///path/to/db.db)
    db_path = DATABASE_URL.replace("sqlite+aiosqlite:///", "").replace("sqlite:///", "")
    if db_path and db_path != ":memory:":
        db_file = Path(db_path)
        db_file.parent.mkdir(parents=True, exist_ok=True)

# Create async engine
# SQLite with NullPool doesn't accept pool_size/max_overflow
if IS_SQLITE:
    engine = create_async_engine(
        DATABASE_URL,
        poolclass=poolclass,
        echo=os.getenv("DATABASE_ECHO", "false").lower() == "true",
        connect_args=connect_args,
    )
else:
    engine = create_async_engine(
        DATABASE_URL,
        poolclass=poolclass,
        pool_size=POOL_SIZE,
        max_overflow=MAX_OVERFLOW,
        pool_pre_ping=True,
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
            # Only commit if session is still in a transaction
            # This allows explicit commits in endpoints while still auto-committing
            # if no explicit commit was made
            if session.in_transaction():
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

