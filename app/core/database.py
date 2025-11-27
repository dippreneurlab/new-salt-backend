from typing import Any, Iterable, List, Optional
from psycopg_pool import AsyncConnectionPool
from psycopg.rows import dict_row

from .config import settings

pool: Optional[AsyncConnectionPool] = None


def _connection_kwargs():
    if settings.postgres_ssl is False:
        return {"sslmode": "disable"}
    return {"sslmode": "require"}


async def get_pool() -> AsyncConnectionPool:
    global pool
    if pool is None:
        conninfo = settings.build_db_url()
        if not conninfo:
            raise RuntimeError("Database configuration is missing. Set DATABASE_URL or POSTGRES_* values.")
        pool = AsyncConnectionPool(conninfo=conninfo, open=False, kwargs=_connection_kwargs())
        await pool.open(wait=True)
    return pool


async def close_pool():
    global pool
    if pool:
        await pool.close()
        pool = None


async def fetch(query: str, params: Iterable[Any] | None = None) -> List[dict]:
    pool = await get_pool()
    async with pool.connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(query, params or [])
            rows = await cur.fetchall()
            await conn.commit()
            return [dict(r) for r in rows]


async def fetchrow(query: str, params: Iterable[Any] | None = None) -> Optional[dict]:
    pool = await get_pool()
    async with pool.connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(query, params or [])
            row = await cur.fetchone()
            await conn.commit()
            return dict(row) if row else None


async def execute(query: str, params: Iterable[Any] | None = None) -> int:
    pool = await get_pool()
    async with pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(query, params or [])
            await conn.commit()
            return cur.rowcount
