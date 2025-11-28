from typing import List, Optional
from app.db import pool as pool_module
from app.schemas.user_schema import UserCreate, UserResponse


async def fetch_users() -> List[UserResponse]:
    async with pool_module.pool.acquire() as conn:
        rows = await conn.fetch("SELECT id, name, email FROM users ORDER BY id")
        return [UserResponse(**dict(row)) for row in rows]


async def create_user(user: UserCreate) -> UserResponse:
    async with pool_module.pool.acquire() as conn:
        row = await conn.fetchrow(
            "INSERT INTO users (name, email) VALUES ($1, $2) RETURNING id, name, email",
            user.name, user.email
        )
        return UserResponse(**dict(row))


async def get_user_by_id(user_id: int) -> Optional[UserResponse]:
    async with pool_module.pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT id, name, email FROM users WHERE id = $1", user_id
        )
        return UserResponse(**dict(row)) if row else None