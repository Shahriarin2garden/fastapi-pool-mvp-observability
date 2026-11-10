#!/usr/bin/env python3
"""
FastAPI Load Test Tool
Clean, concise, and accurate concurrency benchmarker.
"""

import asyncio
import aiohttp
import asyncpg
import statistics
import time
from datetime import datetime

# -------------------------------------------------------------------
# Configuration
# -------------------------------------------------------------------

API_BASE_URL = "http://localhost:8001"
ENDPOINT = "/users/"
CONCURRENCY = 100
TOTAL_REQUESTS = 100

DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'user': 'postgres',
    'password': 'postgres',
    'database': 'fastdb'
}

# -------------------------------------------------------------------
# DB Monitoring
# -------------------------------------------------------------------

async def get_db_state():
    try:
        conn = await asyncpg.connect(**DB_CONFIG)
        result = await conn.fetchrow("""
            SELECT 
                count(*) AS total,
                count(*) FILTER (WHERE state = 'active') AS active,
                count(*) FILTER (WHERE state = 'idle') AS idle
            FROM pg_stat_activity 
            WHERE datname = 'fastdb'
        """)
        await conn.close()
        return dict(result)
    except Exception as e:
        return {"error": str(e)}

# -------------------------------------------------------------------
# API Request Worker
# -------------------------------------------------------------------

async def do_request(session, request_id):
    url = f"{API_BASE_URL}{ENDPOINT}"
    start = time.time()

    try:
        async with session.get(url) as resp:
            await resp.text()
            return {
                "id": request_id,
                "status": resp.status,
                "duration": time.time() - start,
            }
    except Exception as e:
        return {
            "id": request_id,
            "status": 0,
            "duration": 0,
            "error": str(e)
        }

# -------------------------------------------------------------------
# Load Test Runner
# -------------------------------------------------------------------

async def run_load_test():
    print("=== FastAPI Load Test ===")
    print(f"Start Time: {datetime.now()}")
    print(f"Concurrency: {CONCURRENCY}")
    print(f"Total Requests: {TOTAL_REQUESTS}\n")

    # DB state before
    print("DB State Before:")
    print(await get_db_state(), "\n")

    connector = aiohttp.TCPConnector(limit=CONCURRENCY)
    timeout = aiohttp.ClientTimeout(total=30)

    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
        tasks = [do_request(session, i+1) for i in range(TOTAL_REQUESTS)]

        t0 = time.time()
        results = await asyncio.gather(*tasks)
        total_time = time.time() - t0

    # Process results
    successes = [r for r in results if r["status"] == 200]
    failures = [r for r in results if r["status"] != 200]

    latencies = [r["duration"] for r in successes]

    print("=== Results ===")
    print(f"Total Time: {total_time:.2f} s")
    print(f"Success: {len(successes)}/{TOTAL_REQUESTS}")
    print(f"Failure: {len(failures)}")
    print(f"RPS: {TOTAL_REQUESTS / total_time:.2f}")

    if latencies:
        print("\nLatency Distribution:")
        print(f"p50: {statistics.median(latencies)*1000:.1f} ms")
        print(f"p90: {statistics.quantiles(latencies, n=10)[8]*1000:.1f} ms")
        print(f"p99: {statistics.quantiles(latencies, n=100)[98]*1000:.1f} ms")

    print("\nDB State After:")
    print(await get_db_state())

# -------------------------------------------------------------------
# Entry Point
# -------------------------------------------------------------------

if __name__ == "__main__":
    asyncio.run(run_load_test())