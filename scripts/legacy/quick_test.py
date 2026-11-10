#!/usr/bin/env python3
import requests
import time
import threading

def send_requests():
    """Send continuous requests to generate metrics"""
    endpoints = [
        'http://localhost:8001/health',
        'http://localhost:8001/users/',
    ]
    
    for i in range(50):
        for endpoint in endpoints:
            try:
                response = requests.get(endpoint, timeout=2)
                print(f"OK {endpoint} -> {response.status_code}")
            except Exception as e:
                print(f"ERROR {endpoint} -> {e}")
        time.sleep(0.5)

if __name__ == "__main__":
    print("Starting traffic generation...")
    print("This will generate ~300 requests over 50 seconds")
    print("Check rate(http_requests_total[5m]) in Prometheus/Grafana")
    
    # Start multiple threads for concurrent requests
    threads = []
    for i in range(3):
        thread = threading.Thread(target=send_requests)
        threads.append(thread)
        thread.start()
    
    # Wait for all threads to complete
    for thread in threads:
        thread.join()
    
    print("Traffic generation complete!")
    print("Check metrics at:")
    print("   - Prometheus: http://localhost:9090/graph?g0.expr=rate(http_requests_total[5m])")
    print("   - Grafana: http://localhost:3000")