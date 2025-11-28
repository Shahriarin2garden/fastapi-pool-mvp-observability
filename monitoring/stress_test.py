#!/usr/bin/env python3
"""Stress test the database connection pool"""
import asyncio
import asyncpg
import time
from datetime import datetime

DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'user': 'postgres',
    'password': 'postgres',
    'database': 'fastdb',
}

async def stress_test_pool(duration=10, concurrent_workers=20):
    """Stress test the connection pool"""
    print(f"Starting {duration}s stress test with {concurrent_workers} concurrent workers...")
    print("=" * 60)
    
    try:
        # Create connection pool
        pool = await asyncpg.create_pool(
            min_size=2,
            max_size=10,
            **DB_CONFIG
        )
        
        # Statistics tracking
        total_requests = 0
        errors = 0
        start_time = time.time()
        
        async def worker(worker_id):
            """Worker function that performs database operations"""
            worker_requests = 0
            worker_errors = 0
            
            while time.time() - start_time < duration:
                try:
                    async with pool.acquire() as conn:
                        # Perform a mix of operations
                        if worker_requests % 3 == 0:
                            # Read operation
                            await conn.fetchval("SELECT COUNT(*) FROM users")
                        elif worker_requests % 3 == 1:
                            # Read with filter
                            await conn.fetchval("SELECT COUNT(*) FROM users WHERE id > $1", worker_id)
                        else:
                            # Check database version
                            await conn.fetchval("SELECT version()")
                        
                        worker_requests += 1
                        await asyncio.sleep(0.01)  # Small delay to simulate real work
                        
                except Exception as e:
                    worker_errors += 1
                    print(f"Worker {worker_id} error: {e}")
            
            return worker_requests, worker_errors
        
        # Start all workers
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Starting {concurrent_workers} workers...")
        tasks = [worker(i) for i in range(concurrent_workers)]
        
        # Monitor progress
        monitor_task = asyncio.create_task(monitor_progress(pool, start_time, duration))
        
        # Wait for all workers to complete
        results = await asyncio.gather(*tasks)
        monitor_task.cancel()
        
        # Calculate statistics
        total_requests = sum(r[0] for r in results)
        total_errors = sum(r[1] for r in results)
        actual_duration = time.time() - start_time
        
        await pool.close()
        
        # Print results
        print("\\n" + "=" * 60)
        print("STRESS TEST RESULTS")
        print("=" * 60)
        print(f"Duration:            {actual_duration:.2f} seconds")
        print(f"Total Requests:      {total_requests}")
        print(f"Successful Requests: {total_requests - total_errors}")
        print(f"Failed Requests:     {total_errors}")
        print(f"Success Rate:        {((total_requests - total_errors) / total_requests * 100):.1f}%")
        print(f"Requests per Second: {total_requests / actual_duration:.1f} RPS")
        print(f"Concurrent Workers:  {concurrent_workers}")
        print("=" * 60)
        
        if total_errors == 0:
            print("SUCCESS: All requests completed without errors!")
        else:
            print(f"WARNING: {total_errors} requests failed")
        
        return total_requests, total_errors, actual_duration
        
    except Exception as e:
        print(f"STRESS TEST FAILED: {e}")
        return 0, 1, 0

async def monitor_progress(pool, start_time, duration):
    """Monitor progress during stress test"""
    try:
        while time.time() - start_time < duration:
            elapsed = time.time() - start_time
            remaining = duration - elapsed
            progress = (elapsed / duration) * 100
            
            # Get current pool stats
            pool_size = pool.get_size()
            
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Progress: {progress:.1f}% | "
                  f"Pool Size: {pool_size} | Remaining: {remaining:.1f}s")
            
            await asyncio.sleep(2)
    except asyncio.CancelledError:
        pass

async def main():
    """Main function"""
    print("FastAPI Pool MVP - Database Connection Pool Stress Test")
    print("=" * 60)
    
    # Test 1: Light load
    print("\\nTest 1: Light Load (5 workers, 5 seconds)")
    await stress_test_pool(duration=5, concurrent_workers=5)
    
    await asyncio.sleep(2)
    
    # Test 2: Medium load
    print("\\nTest 2: Medium Load (15 workers, 8 seconds)")
    await stress_test_pool(duration=8, concurrent_workers=15)
    
    await asyncio.sleep(2)
    
    # Test 3: Heavy load
    print("\\nTest 3: Heavy Load (25 workers, 10 seconds)")
    await stress_test_pool(duration=10, concurrent_workers=25)
    
    print("\\nAll stress tests completed!")

if __name__ == "__main__":
    asyncio.run(main())