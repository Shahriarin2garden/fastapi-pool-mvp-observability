#!/usr/bin/env python3
"""
Real-time database connection pool monitor
Run this to test DB connections and monitor pool status in real-time
"""
import asyncio
import asyncpg
import time
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', 5432)),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASS', 'postgres'),
    'database': os.getenv('DB_NAME', 'fastdb'),
}

async def test_single_connection():
    """Test a single database connection"""
    try:
        conn = await asyncpg.connect(**DB_CONFIG)
        result = await conn.fetchval("SELECT version()")
        await conn.close()
        return True, result[:50] + "..."
    except Exception as e:
        return False, str(e)

async def test_connection_pool():
    """Test connection pool creation and usage"""
    try:
        pool = await asyncpg.create_pool(
            min_size=2,
            max_size=5,
            **DB_CONFIG
        )
        
        # Test pool usage
        async with pool.acquire() as conn:
            user_count = await conn.fetchval("SELECT COUNT(*) FROM users")
        
        pool_size = pool.get_size()
        await pool.close()
        
        return True, f"Pool size: {pool_size}, Users: {user_count}"
    except Exception as e:
        return False, str(e)

async def monitor_active_connections():
    """Monitor active database connections"""
    try:
        conn = await asyncpg.connect(**DB_CONFIG)
        query = """
        SELECT 
            count(*) as total_connections,
            count(*) FILTER (WHERE state = 'active') as active_connections,
            count(*) FILTER (WHERE state = 'idle') as idle_connections
        FROM pg_stat_activity 
        WHERE datname = $1
        """
        result = await conn.fetchrow(query, DB_CONFIG['database'])
        await conn.close()
        return True, dict(result)
    except Exception as e:
        return False, str(e)

async def stress_test_pool(duration=10, concurrent_requests=5):
    """Stress test the connection pool"""
    print(f"\n🔥 Starting {duration}s stress test with {concurrent_requests} concurrent requests...")
    
    try:
        pool = await asyncpg.create_pool(
            min_size=2,
            max_size=10,
            **DB_CONFIG
        )
        
        async def worker(worker_id):
            requests = 0
            start_time = time.time()
            
            while time.time() - start_time < duration:
                try:
                    async with pool.acquire() as conn:
                        await conn.fetchval("SELECT COUNT(*) FROM users")
                        requests += 1
                        await asyncio.sleep(0.1)  # Small delay
                except Exception as e:
                    print(f"Worker {worker_id} error: {e}")
            
            return requests
        
        # Run concurrent workers
        tasks = [worker(i) for i in range(concurrent_requests)]
        results = await asyncio.gather(*tasks)
        
        total_requests = sum(results)
        await pool.close()
        
        return True, f"Completed {total_requests} requests in {duration}s ({total_requests/duration:.1f} req/s)"
    
    except Exception as e:
        return False, str(e)

def print_status(test_name, success, result):
    """Print formatted test status"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"[{timestamp}] {test_name:<25} {status} - {result}")

async def main():
    """Main monitoring loop"""
    print("🚀 FastAPI Pool MVP - Real-time Database Connection Monitor")
    print("=" * 70)
    print(f"Database: {DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}")
    print("=" * 70)
    
    while True:
        try:
            # Test 1: Single connection
            success, result = await test_single_connection()
            print_status("Single Connection", success, result)
            
            # Test 2: Connection pool
            success, result = await test_connection_pool()
            print_status("Connection Pool", success, result)
            
            # Test 3: Active connections monitoring
            success, result = await monitor_active_connections()
            if success:
                conn_info = f"Total: {result['total_connections']}, Active: {result['active_connections']}, Idle: {result['idle_connections']}"
                print_status("Active Connections", True, conn_info)
            else:
                print_status("Active Connections", False, result)
            
            print("-" * 70)
            
            # Wait before next iteration
            await asyncio.sleep(3)
            
        except KeyboardInterrupt:
            print("\n\n🛑 Monitoring stopped by user")
            break
        except Exception as e:
            print_status("Monitor Error", False, str(e))
            await asyncio.sleep(5)

if __name__ == "__main__":
    print("Press Ctrl+C to stop monitoring\n")
    
    # Ask user for test type
    print("Choose test mode:")
    print("1. Real-time monitoring (default)")
    print("2. Stress test")
    
    choice = input("Enter choice (1-2): ").strip()
    
    if choice == "2":
        duration = int(input("Stress test duration (seconds, default 10): ") or "10")
        concurrent = int(input("Concurrent requests (default 5): ") or "5")
        
        async def run_stress():
            success, result = await stress_test_pool(duration, concurrent)
            print_status("Stress Test", success, result)
        
        asyncio.run(run_stress())
    else:
        asyncio.run(main())