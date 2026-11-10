import asyncpg
from typing import Optional

from app.config import settings
from app.monitoring.metrics import db_pool_max_size

pool: Optional[asyncpg.pool.Pool] = None


async def init_pool():
    global pool
    try:
        pool = await asyncpg.create_pool(
            host=settings.DB_HOST,
            port=settings.DB_PORT,
            user=settings.DB_USER,
            **{"password": settings.DB_PASS},
            database=settings.DB_NAME,
            min_size=settings.POOL_MIN_SIZE,
            max_size=settings.POOL_MAX_SIZE,
            command_timeout=settings.COMMAND_TIMEOUT,
            max_inactive_connection_lifetime=300,
        )
        db_pool_max_size.set(settings.POOL_MAX_SIZE)
        print(
            f"Pool initialized successfully with "
            f"{settings.POOL_MIN_SIZE}-{settings.POOL_MAX_SIZE} connections"
        )
    except Exception as exc:
        print(f"Failed to initialize pool: {exc}")
        raise


async def close_pool():
    global pool
    if pool:
        await pool.close()
