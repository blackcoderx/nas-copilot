from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from pathlib import Path

import asyncpg

from nascopilot.config import settings

_pool: asyncpg.Pool | None = None

_SCHEMA = (Path(__file__).parent / "db" / "schema.sql").read_text()


async def init_pool() -> None:
    global _pool
    _pool = await asyncpg.create_pool(
        dsn=settings.database_url,
        min_size=1,
        max_size=10,
        statement_cache_size=0,  # required for Neon PgBouncer pooled connections
    )
    async with _pool.acquire() as conn:
        await conn.execute(_SCHEMA)


async def close_pool() -> None:
    global _pool
    if _pool:
        await _pool.close()
        _pool = None


@asynccontextmanager
async def get_conn() -> AsyncIterator[asyncpg.pool.PoolConnectionProxy]:
    assert _pool is not None, "DB pool not initialised"
    async with _pool.acquire() as conn:
        yield conn
