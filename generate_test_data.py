#!/usr/bin/env python3
import asyncio
import aiohttp
import time

async def generate_traffic():
    """Generate HTTP requests to test rate(http_requests_total[5m]) query"""
    
    async with aiohttp.ClientSession() as session:
        print("🚀 Generating test traffic for Prometheus metrics...")
        
        # Generate steady traffic for 2 minutes
        start_time = time.time()
        request_count = 0
        
        while time.time() - start_time < 120:  # Run for 2 minutes
            try:
                # Mix of different endpoints
                endpoints = [
                    'http://localhost:8001/health',
                    'http://localhost:8001/users/',
                    'http://localhost:8001/users/1'
                ]
                
                # Send requests to different endpoints
                for endpoint in endpoints:
                    async with session.get(endpoint) as response:
                        request_count += 1
                        if request_count % 10 == 0:
                            elapsed = time.time() - start_time
                            rps = request_count / elapsed
                            print(f"📊 Sent {request_count} requests in {elapsed:.1f}s ({rps:.1f} RPS)")
                
                await asyncio.sleep(0.1)  # 10 requests per second
                
            except Exception as e:
                print(f"❌ Error: {e}")
                await asyncio.sleep(1)
        
        print(f"✅ Completed! Generated {request_count} requests")
        print("📈 Check Grafana dashboard: http://localhost:3000")
        print("🔍 Check Prometheus: http://localhost:9090/graph?g0.expr=rate(http_requests_total[5m])")

if __name__ == "__main__":
    asyncio.run(generate_traffic())