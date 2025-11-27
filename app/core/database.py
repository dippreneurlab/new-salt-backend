import sys
import traceback
from typing import Any, Iterable, List, Optional
from psycopg_pool import AsyncConnectionPool
from psycopg.rows import dict_row
from psycopg import OperationalError, DatabaseError

from .config import settings

pool: Optional[AsyncConnectionPool] = None


def _connection_kwargs():
    """Build connection kwargs for psycopg"""
    kwargs = {}
    
    # SSL configuration
    if settings.postgres_ssl is False:
        kwargs["sslmode"] = "disable"
    else:
        kwargs["sslmode"] = "require"
    
    # Connection timeouts (important for Cloud Run)
    kwargs["connect_timeout"] = 10  # 10 seconds to establish connection
    
    # Application name for debugging
    kwargs["application_name"] = "quotehub_backend"
    
    return kwargs


async def get_pool() -> AsyncConnectionPool:
    """
    Get or create the database connection pool.
    Optimized for Cloud Run with proper error handling.
    """
    global pool
    
    if pool is not None:
        return pool
    
    conninfo = settings.build_db_url()
    
    if not conninfo:
        raise RuntimeError(
            "Database configuration is missing. "
            "Set DATABASE_URL or POSTGRES_* environment variables."
        )
    
    # Mask password for logging
    try:
        safe_conninfo = conninfo.split('@')[0].rsplit(':', 1)[0] + ":****@" + conninfo.split('@')[1]
    except:
        safe_conninfo = "postgresql://****"
    
    print(f"Initializing database pool...")
    print(f"Connection: {safe_conninfo}")
    print(f"SSL Mode: {'disabled' if settings.postgres_ssl is False else 'required'}")
    
    try:
        # Create pool with Cloud Run optimized settings
        pool = AsyncConnectionPool(
            conninfo=conninfo,
            open=False,  # Don't open immediately
            kwargs=_connection_kwargs(),
            min_size=1,  # Minimum connections (Cloud Run: keep low)
            max_size=10,  # Maximum connections
            timeout=30,  # Wait timeout for getting a connection
            max_idle=300,  # Close idle connections after 5 minutes
            max_lifetime=3600,  # Recycle connections after 1 hour
        )
        
        # Open the pool with timeout
        print("Opening connection pool...")
        await pool.open(wait=True, timeout=30)
        
        # Test the connection
        print("Testing database connection...")
        async with pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute("SELECT version()")
                version = await cur.fetchone()
                print(f"✓ Connected to: {version[0][:80]}...")
        
        print("✓ Database pool initialized successfully")
        return pool
        
    except OperationalError as e:
        error_msg = str(e)
        print("=" * 60)
        print("DATABASE CONNECTION ERROR (OperationalError):")
        print(f"  {error_msg}")
        print("=" * 60)
        
        # Provide helpful diagnostics
        if "timeout" in error_msg.lower():
            print("\n🔍 DIAGNOSIS: Connection timeout")
            print("   Possible causes:")
            print("   1. Cloud SQL instance is not running")
            print("   2. Wrong CLOUD_SQL_CONNECTION_NAME")
            print("   3. Cloud Run service not connected to Cloud SQL")
            print("   4. Firewall blocking connection")
            
        elif "password" in error_msg.lower() or "authentication" in error_msg.lower():
            print("\n🔍 DIAGNOSIS: Authentication failed")
            print("   Possible causes:")
            print("   1. Wrong POSTGRES_USER")
            print("   2. Wrong POSTGRES_PASSWORD")
            print("   3. User doesn't have access to the database")
            
        elif "database" in error_msg.lower() and "does not exist" in error_msg.lower():
            print("\n🔍 DIAGNOSIS: Database not found")
            print(f"   The database '{settings.postgres_db}' does not exist")
            print("   Create it or check POSTGRES_DB environment variable")
            
        elif "connection refused" in error_msg.lower():
            print("\n🔍 DIAGNOSIS: Connection refused")
            print("   Possible causes:")
            print("   1. Wrong POSTGRES_HOST")
            print("   2. Wrong POSTGRES_PORT")
            print("   3. Database server not running")
        
        print("\nCurrent configuration:")
        print(f"  POSTGRES_HOST: {settings.postgres_host}")
        print(f"  POSTGRES_PORT: {settings.postgres_port}")
        print(f"  POSTGRES_DB: {settings.postgres_db}")
        print(f"  POSTGRES_USER: {settings.postgres_user}")
        print(f"  POSTGRES_PASSWORD: {'set' if settings.postgres_password else 'NOT SET'}")
        print(f"  CLOUD_SQL_CONNECTION_NAME: {settings.cloud_sql_connection_name}")
        print(f"  DATABASE_URL: {'set' if settings.database_url else 'NOT SET'}")
        print("=" * 60)
        
        traceback.print_exc(file=sys.stdout)
        raise
        
    except DatabaseError as e:
        print("=" * 60)
        print("DATABASE ERROR:")
        print(f"  {str(e)}")
        print("=" * 60)
        traceback.print_exc(file=sys.stdout)
        raise
        
    except Exception as e:
        print("=" * 60)
        print("UNEXPECTED ERROR:")
        print(f"  Type: {type(e).__name__}")
        print(f"  Message: {str(e)}")
        print("=" * 60)
        traceback.print_exc(file=sys.stdout)
        raise


async def close_pool():
    """Close the database connection pool"""
    global pool
    
    if pool:
        print("Closing database pool...")
        await pool.close()
        pool = None
        print("✓ Database pool closed")


async def fetch(query: str, params: Iterable[Any] | None = None) -> List[dict]:
    """Execute a SELECT query and return all rows as dictionaries"""
    pool_instance = await get_pool()
    async with pool_instance.connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(query, params or [])
            rows = await cur.fetchall()
            return [dict(r) for r in rows]


async def fetchrow(query: str, params: Iterable[Any] | None = None) -> Optional[dict]:
    """Execute a SELECT query and return a single row as a dictionary"""
    pool_instance = await get_pool()
    async with pool_instance.connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(query, params or [])
            row = await cur.fetchone()
            return dict(row) if row else None


async def execute(query: str, params: Iterable[Any] | None = None) -> int:
    """Execute an INSERT/UPDATE/DELETE query and return affected row count"""
    pool_instance = await get_pool()
    async with pool_instance.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(query, params or [])
            await conn.commit()
            return cur.rowcount


async def execute_many(query: str, params_list: List[Iterable[Any]]) -> int:
    """Execute a query multiple times with different parameters (bulk insert/update)"""
    pool_instance = await get_pool()
    async with pool_instance.connection() as conn:
        async with conn.cursor() as cur:
            await cur.executemany(query, params_list)
            await conn.commit()
            return cur.rowcount