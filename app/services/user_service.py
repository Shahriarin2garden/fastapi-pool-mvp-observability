from typing import List, Optional
import time
from app.db import pool as pool_module
from app.schemas.user_schema import UserCreate, UserResponse
from app.monitoring.metrics import (
    db_query_duration, db_connection_acquire_duration,
    db_pool_size, db_query_errors, db_connection_errors
)


async def fetch_users() -> List[UserResponse]:
    acquire_start = time.time()
    try:
        async with pool_module.pool.acquire() as conn:
            db_connection_acquire_duration.observe(time.time() - acquire_start)
            db_pool_size.set(pool_module.pool.get_size())
            
            query_start = time.time()
            rows = await conn.fetch("SELECT id, name, email FROM users ORDER BY id")
            db_query_duration.observe(time.time() - query_start)
            return [UserResponse(**dict(row)) for row in rows]
    except Exception as e:
        db_query_errors.inc()
        raise


async def create_user(user: UserCreate) -> UserResponse:
    acquire_start = time.time()
    try:
        async with pool_module.pool.acquire() as conn:
            db_connection_acquire_duration.observe(time.time() - acquire_start)
            db_pool_size.set(pool_module.pool.get_size())
            
            query_start = time.time()
            row = await conn.fetchrow(
                "INSERT INTO users (name, email) VALUES ($1, $2) RETURNING id, name, email",
                user.name, user.email
            )
            db_query_duration.observe(time.time() - query_start)
            return UserResponse(**dict(row))
    except Exception as e:
        db_query_errors.inc()
        raise


async def get_user_by_id(user_id: int) -> Optional[UserResponse]:
    acquire_start = time.time()
    try:
        async with pool_module.pool.acquire() as conn:
            db_connection_acquire_duration.observe(time.time() - acquire_start)
            db_pool_size.set(pool_module.pool.get_size())
            
            query_start = time.time()
            row = await conn.fetchrow(
                "SELECT id, name, email FROM users WHERE id = $1", user_id
            )
            db_query_duration.observe(time.time() - query_start)
            return UserResponse(**dict(row)) if row else None
    except Exception as e:
        db_query_errors.inc()
        raise