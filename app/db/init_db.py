from app.db import pool as pool_module

CREATE_USERS_TABLE = """
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""


async def ensure_tables():
    if pool_module.pool is None:
        raise RuntimeError("Database pool is not initialized")
    try:
        async with pool_module.pool.acquire() as conn:
            await conn.execute(CREATE_USERS_TABLE)
            print("Tables created successfully")
    except Exception as e:
        print(f"Failed to create tables: {e}")
        raise