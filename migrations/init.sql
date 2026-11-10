-- Initial database schema
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS orders (
    id SERIAL PRIMARY KEY,
    customer_email TEXT NOT NULL,
    item TEXT NOT NULL,
    quantity INT NOT NULL CHECK (quantity > 0),
    amount_cents INT NOT NULL CHECK (amount_cents >= 0),
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Create index on email for faster lookups
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);