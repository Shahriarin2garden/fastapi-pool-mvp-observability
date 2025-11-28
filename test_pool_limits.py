#!/usr/bin/env python3
"""Test connection pool limits and behavior under extreme load"""
import asyncio
import asyncpg
import time
from datetime import datetime

DB_CONFIG = {
    'host': 'db',  # Docker service name
    'port': 5432,
    'user': 'postgres',
    'password': 'postgres',
    'database': 'fastdb',
}

async def test_pool_scaling():
    """Test how pool scales from min to max connections"""
    print("=" * 60)
    print("CONNECTION POOL SCALING TEST")
    print("=" * 60)
    
    # Create pool with same settings as your app
    pool = await asyncpg.create_pool(
        min_size=2,
        max_size=10,
        command_timeout=10,
        max_inactive_connection_lifetime=300,
        **DB_CONFIG
    )
    
    print(f"Pool created: min_size=2, max_size=10")
    print(f"Initial pool size: {pool.get_size()}")
    
    connections = []
    
    try:
        # Gradually acquire connections to see scaling
        for i in range(15):  # Try to get more than max
            try:
                print(f"\nAttempting to acquire connection {i+1}...")
                conn = await asyncio.wait_for(pool.acquire(), timeout=1.0)
                connections.append(conn)
                print(f"✅ Acquired connection {i+1}")
                print(f"Current pool size: {pool.get_size()}")
                
                # Check database connections
                result = await conn.fetchrow("""
                    SELECT count(*) as total_connections
                    FROM pg_stat_activity 
                    WHERE datname = 'fastdb'
                """)
                print(f"Database shows {result['total_connections']} total connections")
                
            except asyncio.TimeoutError:
                print(f"❌ Timeout acquiring connection {i+1} (pool limit reached)")
                break
            except Exception as e:
                print(f"❌ Error acquiring connection {i+1}: {e}")
                break
        
        print(f"\n📊 Final Results:")
        print(f"Connections acquired: {len(connections)}")
        print(f"Pool size: {pool.get_size()}")
        
    finally:
        # Release all connections
        for conn in connections:
            await pool.release(conn)
        await pool.close()

async def test_concurrent_load_with_monitoring():
    """Test concurrent load while monitoring pool behavior"""
    print("\n" + "=" * 60)
    print("CONCURRENT LOAD TEST WITH POOL MONITORING")
    print("=" * 60)
    
    pool = await asyncpg.create_pool(
        min_size=2,
        max_size=10,
        **DB_CONFIG
    )
    
    async def worker(worker_id, duration=5):
        """Worker that performs database operations"""
        operations = 0
        start_time = time.time()
        
        while time.time() - start_time < duration:
            try:
                async with pool.acquire() as conn:
                    # Simulate different types of queries
                    if operations % 3 == 0:
                        await conn.fetchval("SELECT COUNT(*) FROM users")
                    elif operations % 3 == 1:
                        await conn.fetchval("SELECT version()")
                    else:
                        await conn.fetchval("SELECT current_timestamp")
                    
                    operations += 1
                    await asyncio.sleep(0.01)  # Small delay
                    
            except Exception as e:
                print(f"Worker {worker_id} error: {e}")
        
        return operations
    
    async def monitor_pool():
        """Monitor pool statistics"""
        while True:
            try:
                # Get pool stats
                pool_size = pool.get_size()
                
                # Get database connection count
                async with pool.acquire() as conn:
                    result = await conn.fetchrow("""
                        SELECT 
                            count(*) as total_connections,
                            count(*) FILTER (WHERE state = 'active') as active_connections,
                            count(*) FILTER (WHERE state = 'idle') as idle_connections
                        FROM pg_stat_activity 
                        WHERE datname = 'fastdb'
                    """)
                
                print(f"[{datetime.now().strftime('%H:%M:%S')}] "
                      f"Pool Size: {pool_size} | "
                      f"DB Total: {result['total_connections']} | "
                      f"Active: {result['active_connections']} | "
                      f"Idle: {result['idle_connections']}")
                
                await asyncio.sleep(1)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Monitor error: {e}")
                await asyncio.sleep(1)
    
    # Start monitoring
    monitor_task = asyncio.create_task(monitor_pool())
    
    # Test different load levels
    for num_workers in [5, 15, 25, 50]:
        print(f"\n🚀 Testing with {num_workers} concurrent workers...")
        
        start_time = time.time()
        tasks = [worker(i, duration=3) for i in range(num_workers)]
        results = await asyncio.gather(*tasks)
        duration = time.time() - start_time
        
        total_operations = sum(results)
        print(f"Workers: {num_workers} | Operations: {total_operations} | "
              f"Duration: {duration:.2f}s | OPS: {total_operations/duration:.1f}")
        
        await asyncio.sleep(2)  # Cool down between tests
    
    monitor_task.cancel()
    await pool.close()

async def test_pool_exhaustion():
    """Test what happens when pool is exhausted"""
    print("\n" + "=" * 60)
    print("POOL EXHAUSTION TEST")
    print("=" * 60)
    
    pool = await asyncpg.create_pool(
        min_size=2,
        max_size=5,  # Smaller pool for easier exhaustion
        **DB_CONFIG
    )
    
    print("Created pool with max_size=5")
    
    async def long_running_task(task_id):
        """Task that holds connection for a long time"""
        try:
            async with pool.acquire() as conn:
                print(f"Task {task_id} acquired connection")
                await conn.fetchval("SELECT pg_sleep(10)")  # Hold for 10 seconds
                print(f"Task {task_id} completed")
        except Exception as e:
            print(f"Task {task_id} failed: {e}")
    
    async def quick_task(task_id):
        """Quick task that should wait for available connection"""
        try:
            print(f"Quick task {task_id} waiting for connection...")
            start_time = time.time()
            async with pool.acquire() as conn:
                wait_time = time.time() - start_time
                print(f"Quick task {task_id} got connection after {wait_time:.2f}s")
                await conn.fetchval("SELECT 1")
        except Exception as e:
            print(f"Quick task {task_id} failed: {e}")
    
    # Start 5 long-running tasks to exhaust pool
    long_tasks = [long_running_task(i) for i in range(5)]
    
    # Start them and wait a bit
    asyncio.create_task(asyncio.gather(*long_tasks))
    await asyncio.sleep(2)  # Let them acquire connections
    
    # Now try quick tasks that should wait
    print("\nStarting quick tasks that should wait...")
    quick_tasks = [quick_task(i) for i in range(3)]
    await asyncio.gather(*quick_tasks)
    
    await pool.close()

async def main():
    """Run all pool tests"""
    print("FastAPI Connection Pool - Advanced Testing")
    print("Testing pool behavior, scaling, and limits")
    
    try:
        await test_pool_scaling()
        await test_concurrent_load_with_monitoring()
        await test_pool_exhaustion()
        
        print(f"\n🎉 All pool tests completed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())