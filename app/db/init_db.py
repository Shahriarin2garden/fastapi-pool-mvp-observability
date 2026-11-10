from app.db import pool as pool_module

CREATE_USERS_TABLE = """
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

CREATE_ORDERS_TABLE = """
CREATE TABLE IF NOT EXISTS orders (
    id SERIAL PRIMARY KEY,
    customer_email TEXT NOT NULL,
    item TEXT NOT NULL,
    quantity INT NOT NULL CHECK (quantity > 0),
    amount_cents INT NOT NULL CHECK (amount_cents >= 0),
    created_at TIMESTAMPTZ DEFAULT now()
);
"""


async def ensure_tables():
    if pool_module.pool is None:
        raise RuntimeError("Database pool is not initialized")
    try:
        async with pool_module.pool.acquire() as conn:
            await conn.execute(CREATE_USERS_TABLE)
            await conn.execute(CREATE_ORDERS_TABLE)
            print("Tables created successfully")
    except Exception as e:
        print(f"Failed to create tables: {e}")
        raise