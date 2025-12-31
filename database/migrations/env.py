"""
Alembic environment configuration.
"""

from logging.config import fileConfig
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config
import asyncio

from alembic import context
import os
import sys

# Add parent directory to path to import models
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

# Import Base and models
from database.session import Base
from database.models import User, Reconciliation, ReconciliationResult, AuditLog

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Get database URL from environment
database_url = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://user:password@localhost/dbname"
)

# Convert postgresql:// to postgresql+asyncpg:// if needed
if database_url.startswith("postgresql://"):
    database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)

# Handle SSL parameters for asyncpg
# asyncpg doesn't support sslmode/channel_binding in URL, so we remove them
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
parsed = urlparse(database_url)
query_params = parse_qs(parsed.query)
ssl_mode = query_params.pop('sslmode', None)
channel_binding = query_params.pop('channel_binding', None)

# Reconstruct URL without sslmode/channel_binding
new_query = urlencode(query_params, doseq=True)
clean_url = urlunparse((
    parsed.scheme,
    parsed.netloc,
    parsed.path,
    parsed.params,
    new_query,
    parsed.fragment
))

# Set the sqlalchemy.url in the config
config.set_main_option("sqlalchemy.url", clean_url)

# Store SSL requirement for engine creation
_ssl_required = ssl_mode and ssl_mode[0] == 'require'

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    # Get engine config
    connect_args = {}
    if _ssl_required:
        # Configure SSL for asyncpg
        import ssl
        connect_args['ssl'] = ssl.create_default_context()
    
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        connect_args=connect_args,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""

    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

