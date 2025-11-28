#!/usr/bin/env python3
"""Real-time database connection monitor"""
import asyncio
import asyncpg
import time
from datetime import datetime
import sys

DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'user': 'postgres',
    'password': 'postgres',
    'database': 'fastdb',
}

async def get_db_stats():
    """Get current database statistics"""
    try:
        conn = await asyncpg.connect(**DB_CONFIG)
        
        # Get connection stats
        conn_stats = await conn.fetchrow("""
            SELECT 
                count(*) as total_connections,
                count(*) FILTER (WHERE state = 'active') as active_connections,
                count(*) FILTER (WHERE state = 'idle') as idle_connections
            FROM pg_stat_activity 
            WHERE datname = $1
        """, DB_CONFIG['database'])
        
        # Get user count
        user_count = await conn.fetchval("SELECT COUNT(*) FROM users")
        
        # Get database size
        db_size = await conn.fetchval("""
            SELECT pg_size_pretty(pg_database_size($1))
        """, DB_CONFIG['database'])
        
        await conn.close()
        
        return {
            'success': True,
            'total_connections': conn_stats['total_connections'],
            'active_connections': conn_stats['active_connections'], 
            'idle_connections': conn_stats['idle_connections'],
            'user_count': user_count,
            'db_size': db_size
        }
        
    except Exception as e:
        return {'success': False, 'error': str(e)}

async def test_pool_performance():
    """Test connection pool performance"""
    try:
        pool = await asyncpg.create_pool(
            min_size=2, max_size=10, **DB_CONFIG
        )
        
        start_time = time.time()
        
        # Perform 10 concurrent queries
        async def query_task():
            async with pool.acquire() as conn:
                return await conn.fetchval("SELECT COUNT(*) FROM users")
        
        tasks = [query_task() for _ in range(10)]
        results = await asyncio.gather(*tasks)
        
        elapsed = time.time() - start_time
        await pool.close()
        
        return {
            'success': True,
            'queries': len(results),
            'time': elapsed,
            'qps': len(results) / elapsed
        }
        
    except Exception as e:
        return {'success': False, 'error': str(e)}

def clear_screen():
    """Clear terminal screen"""
    import os
    os.system('cls' if os.name == 'nt' else 'clear')

async def monitor_loop():
    """Main monitoring loop"""
    iteration = 0
    
    while True:
        try:
            iteration += 1
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Clear screen every 10 iterations for better readability
            if iteration % 10 == 1:
                clear_screen()
            
            print(f"\\n[{timestamp}] FastAPI Pool MVP - DB Monitor (Iteration {iteration})")
            print("=" * 60)
            
            # Get database statistics
            db_stats = await get_db_stats()
            
            if db_stats['success']:
                print(f"Database Status:     [CONNECTED]")
                print(f"Total Connections:   {db_stats['total_connections']}")
                print(f"Active Connections:  {db_stats['active_connections']}")
                print(f"Idle Connections:    {db_stats['idle_connections']}")
                print(f"Users in Database:   {db_stats['user_count']}")
                print(f"Database Size:       {db_stats['db_size']}")
            else:
                print(f"Database Status:     [ERROR] {db_stats['error']}")
            
            # Test pool performance every 5 iterations
            if iteration % 5 == 0:
                print("\\nTesting Pool Performance...")
                perf_stats = await test_pool_performance()
                
                if perf_stats['success']:
                    print(f"Pool Test:           [OK] {perf_stats['queries']} queries in {perf_stats['time']:.3f}s")
                    print(f"Queries per Second:  {perf_stats['qps']:.1f} QPS")
                else:
                    print(f"Pool Test:           [ERROR] {perf_stats['error']}")
            
            print("-" * 60)
            print("Press Ctrl+C to stop monitoring...")
            
            # Wait 3 seconds before next iteration
            await asyncio.sleep(3)
            
        except KeyboardInterrupt:
            print("\\n\\nMonitoring stopped by user.")
            break
        except Exception as e:
            print(f"\\n[ERROR] Monitor error: {e}")
            await asyncio.sleep(5)

if __name__ == "__main__":
    print("Starting real-time database monitor...")
    print("This will monitor your FastAPI Pool MVP database connection.")
    print("\\nPress Ctrl+C to stop.\\n")
    
    try:
        asyncio.run(monitor_loop())
    except KeyboardInterrupt:
        print("\\nMonitor stopped.")
        sys.exit(0)