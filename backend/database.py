"""Async SQLAlchemy engine + session factory."""
import os
from collections.abc import AsyncIterator

from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

# "sqlite+aiosqlite" = SQLite accessed through the async aiosqlite driver.
# Overridable via env var so Docker can point it at a mounted volume.
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./triage.db")

engine = create_async_engine(DATABASE_URL, echo=False)


@event.listens_for(engine.sync_engine, "connect")
def enable_sqlite_foreign_keys(dbapi_connection, connection_record):
    # SQLite does NOT enforce foreign keys unless you ask it to, per connection.
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


# expire_on_commit=False: after commit(), objects keep their loaded attributes.
# Otherwise touching them would trigger a lazy DB load, which fails in async code.
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    """Parent class for all ORM models."""


async def get_db() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency: one session per request, always closed afterwards."""
    async with AsyncSessionLocal() as session:
        yield session