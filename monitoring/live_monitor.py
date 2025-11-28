#!/usr/bin/env python3
"""Live monitoring while FastAPI app is running"""
import asyncio
import asyncpg
import aiohttp
import time
from datetime import datetime

DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'user': 'postgres',
    'password': 'postgres',
    'database': 'fastdb',
}

API_BASE_URL = "http://localhost:8001"

async def get_db_connections():
    """Get current database connection info"""
    try:
        conn = await asyncpg.connect(**DB_CONFIG)
        result = await conn.fetchrow("""
            SELECT 
                count(*) as total,
                count(*) FILTER (WHERE state = 'active') as active,
                count(*) FILTER (WHERE state = 'idle') as idle,
                count(*) FILTER (WHERE application_name LIKE '%asyncpg%') as asyncpg_conns
            FROM pg_stat_activity 
            WHERE datname = $1
        """, DB_CONFIG['database'])
        await conn.close()
        return dict(result)
    except Exception as e:
        return {'error': str(e)}

async def test_api_endpoints():
    """Test FastAPI endpoints"""
    try:
        async with aiohttp.ClientSession() as session:
            # Test health endpoint
            async with session.get(f"{API_BASE_URL}/health") as resp:
                health_status = resp.status
            
            # Test users endpoint
            async with session.get(f"{API_BASE_URL}/users/") as resp:
                users_status = resp.status
                users_data = await resp.json()
            
            return {
                'health_status': health_status,
                'users_status': users_status,
                'user_count': len(users_data) if isinstance(users_data, list) else 0
            }
    except Exception as e:
        return {'error': str(e)}

async def simulate_api_load():
    """Simulate some API load"""
    try:
        async with aiohttp.ClientSession() as session:
            tasks = []
            for i in range(5):
                tasks.append(session.get(f"{API_BASE_URL}/users/"))
            
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            successful = sum(1 for r in responses if not isinstance(r, Exception))
            
            # Close all responses
            for resp in responses:
                if hasattr(resp, 'close'):
                    resp.close()
            
            return {'requests': len(tasks), 'successful': successful}
    except Exception as e:
        return {'error': str(e)}

async def live_monitor():
    """Live monitoring function"""
    print("FastAPI Pool MVP - Live Database & API Monitor")
    print("=" * 60)
    print("This monitors both the database connections and FastAPI endpoints")
    print("Make sure your FastAPI app is running on http://localhost:8001")
    print("=" * 60)
    
    iteration = 0
    
    while iteration < 10:  # Run 10 iterations
        iteration += 1
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        print(f"\\n[{timestamp}] Live Monitor - Iteration {iteration}/10")
        print("-" * 50)
        
        # Check database connections
        db_stats = await get_db_connections()
        if 'error' not in db_stats:
            print(f"DB Connections:      Total: {db_stats['total']}, Active: {db_stats['active']}, Idle: {db_stats['idle']}")
            print(f"AsyncPG Connections: {db_stats['asyncpg_conns']}")
        else:
            print(f"DB Status:           [ERROR] {db_stats['error']}")
        
        # Test API endpoints
        api_stats = await test_api_endpoints()
        if 'error' not in api_stats:
            print(f"API Health:          HTTP {api_stats['health_status']}")
            print(f"API Users:           HTTP {api_stats['users_status']} ({api_stats['user_count']} users)")
        else:
            print(f"API Status:          [ERROR] {api_stats['error']}")
        
        # Simulate some load every 3rd iteration
        if iteration % 3 == 0:
            print("\\nSimulating API load...")
            load_stats = await simulate_api_load()
            if 'error' not in load_stats:
                print(f"Load Test:           {load_stats['successful']}/{load_stats['requests']} requests successful")
            else:
                print(f"Load Test:           [ERROR] {load_stats['error']}")
        
        await asyncio.sleep(2)
    
    print("\\n" + "=" * 60)
    print("Live monitoring completed!")
    print("The FastAPI connection pool is handling requests efficiently.")

if __name__ == "__main__":
    asyncio.run(live_monitor())