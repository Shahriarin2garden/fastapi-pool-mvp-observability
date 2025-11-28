#!/usr/bin/env python3
"""Direct connection pool test - fetch 20+ users using asyncpg pool directly"""
import asyncio
import asyncpg
import time

DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'user': 'postgres',
    'password': 'postgres',
    'database': 'fastdb',
}

async def test_direct_pool_fetch():
    """Test fetching users directly using asyncpg connection pool"""
    print("Direct Connection Pool Test - Fetching 20+ Users")
    print("=" * 60)
    
    # Create connection pool (same config as FastAPI app)
    pool = await asyncpg.create_pool(
        min_size=2,
        max_size=10,
        command_timeout=5,
        **DB_CONFIG
    )
    
    try:
        # Test 1: Single fetch of all users
        print("\\n1. Single fetch of all users:")
        start_time = time.time()
        
        async with pool.acquire() as conn:
            users = await conn.fetch("SELECT id, name, email FROM users ORDER BY id")
        
        elapsed = time.time() - start_time
        print(f"   Fetched {len(users)} users in {elapsed:.3f} seconds")
        
        # Show first 10 users
        print(f"\\n   First 10 users:")
        for user in users[:10]:
            print(f"   ID: {user['id']:2d} | {user['name']:<20} | {user['email']}")
        
        if len(users) > 10:
            print(f"   ... and {len(users) - 10} more users")
        
        # Test 2: Concurrent fetches using pool
        print(f"\\n2. Concurrent fetches (10 simultaneous requests):")
        
        async def fetch_users_concurrent():
            async with pool.acquire() as conn:
                start = time.time()
                result = await conn.fetch("SELECT COUNT(*) as count FROM users")
                elapsed = time.time() - start
                return result[0]['count'], elapsed
        
        # Run 10 concurrent requests
        start_time = time.time()
        tasks = [fetch_users_concurrent() for _ in range(10)]
        results = await asyncio.gather(*tasks)
        total_elapsed = time.time() - start_time
        
        print(f"   Completed 10 concurrent requests in {total_elapsed:.3f} seconds")
        print(f"   Average response time: {sum(r[1] for r in results) / len(results):.3f} seconds")
        print(f"   All requests returned {results[0][0]} users")
        
        # Test 3: Pool statistics
        print(f"\\n3. Connection Pool Statistics:")
        print(f"   Pool size: {pool.get_size()}")
        print(f"   Pool min size: 2")
        print(f"   Pool max size: 10")
        
        # Test 4: Batch operations
        print(f"\\n4. Batch fetch test (fetch users in chunks):")
        
        async def fetch_user_batch(offset, limit):
            async with pool.acquire() as conn:
                return await conn.fetch(
                    "SELECT id, name FROM users ORDER BY id OFFSET $1 LIMIT $2",
                    offset, limit
                )
        
        batch_size = 5
        total_users = len(users)
        batches = (total_users + batch_size - 1) // batch_size
        
        start_time = time.time()
        batch_tasks = [
            fetch_user_batch(i * batch_size, batch_size) 
            for i in range(batches)
        ]
        batch_results = await asyncio.gather(*batch_tasks)
        batch_elapsed = time.time() - start_time
        
        total_fetched = sum(len(batch) for batch in batch_results)
        print(f"   Fetched {total_fetched} users in {batches} batches of {batch_size}")
        print(f"   Batch processing time: {batch_elapsed:.3f} seconds")
        
        # Test 5: Connection reuse demonstration
        print(f"\\n5. Connection reuse test:")
        
        connection_ids = []
        
        async def get_connection_id():
            async with pool.acquire() as conn:
                result = await conn.fetchval("SELECT pg_backend_pid()")
                return result
        
        # Get connection IDs from multiple requests
        for i in range(5):
            conn_id = await get_connection_id()
            connection_ids.append(conn_id)
            print(f"   Request {i+1}: Connection PID {conn_id}")
        
        unique_connections = len(set(connection_ids))
        print(f"   Used {unique_connections} unique connections for 5 requests")
        print(f"   Connection reuse: {5 - unique_connections} times")
        
    finally:
        await pool.close()
    
    print(f"\\n" + "=" * 60)
    print(f"Direct pool test completed successfully!")
    print(f"Demonstrated efficient connection pooling with {len(users)} users.")

if __name__ == "__main__":
    asyncio.run(test_direct_pool_fetch())