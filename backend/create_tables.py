"""Create the database (if it doesn't exist) and all tables from SQLAlchemy models.

Run this once to initialize the database:
    python create_tables.py
"""
import asyncio
from urllib.parse import urlparse, urlunparse

import asyncpg
from sqlalchemy.ext.asyncio import create_async_engine

from app.config import get_settings
from app.models.db import Base


def _parse_db_url(database_url: str) -> tuple[str, str]:
    """Extract the database name and build a server-level connection URL.

    Returns:
        (server_url, db_name) where server_url connects to the default
        'postgres' database on the same server.
    """
    # DATABASE_URL format: postgresql+asyncpg://user:pass@host:port/dbname
    # Strip the SQLAlchemy dialect prefix for asyncpg
    raw_url = database_url.replace("postgresql+asyncpg://", "postgresql://")
    parsed = urlparse(raw_url)
    db_name = parsed.path.lstrip("/")
    # Build URL pointing to the default 'postgres' database
    server_parsed = parsed._replace(path="/postgres")
    server_url = urlunparse(server_parsed)
    return server_url, db_name


async def _ensure_database_exists(database_url: str) -> None:
    """Create the target database if it doesn't already exist."""
    server_url, db_name = _parse_db_url(database_url)

    conn = await asyncpg.connect(server_url)
    try:
        # Check if the database exists
        exists = await conn.fetchval(
            "SELECT 1 FROM pg_database WHERE datname = $1", db_name
        )
        if not exists:
            # Use double-quote escaping for the DB name (can't use parameterized DDL)
            await conn.execute(f'CREATE DATABASE "{db_name}"')
            print(f'Database "{db_name}" created successfully.')
        else:
            print(f'Database "{db_name}" already exists.')
    finally:
        await conn.close()


async def create_all_tables():
    settings = get_settings()

    # Step 1: Ensure the database exists
    await _ensure_database_exists(settings.DATABASE_URL)

    # Step 2: Create all tables
    engine = create_async_engine(settings.DATABASE_URL)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()

    print("All tables created successfully.")


if __name__ == "__main__":
    asyncio.run(create_all_tables())
