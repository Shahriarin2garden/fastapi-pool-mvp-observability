#!/usr/bin/env python3
"""Populate database with 20+ users and fetch them using connection pooling"""
import asyncio
import requests
import time
from datetime import datetime

API_BASE_URL = "http://localhost:8001"

# Sample user data
USERS_DATA = [
    {"name": "Alice Johnson", "email": "alice.johnson@example.com"},
    {"name": "Bob Smith", "email": "bob.smith@example.com"},
    {"name": "Charlie Brown", "email": "charlie.brown@example.com"},
    {"name": "Diana Prince", "email": "diana.prince@example.com"},
    {"name": "Edward Norton", "email": "edward.norton@example.com"},
    {"name": "Fiona Green", "email": "fiona.green@example.com"},
    {"name": "George Wilson", "email": "george.wilson@example.com"},
    {"name": "Helen Davis", "email": "helen.davis@example.com"},
    {"name": "Ivan Petrov", "email": "ivan.petrov@example.com"},
    {"name": "Julia Roberts", "email": "julia.roberts@example.com"},
    {"name": "Kevin Hart", "email": "kevin.hart@example.com"},
    {"name": "Linda Martinez", "email": "linda.martinez@example.com"},
    {"name": "Michael Jordan", "email": "michael.jordan@example.com"},
    {"name": "Nancy Drew", "email": "nancy.drew@example.com"},
    {"name": "Oscar Wilde", "email": "oscar.wilde@example.com"},
    {"name": "Patricia Lee", "email": "patricia.lee@example.com"},
    {"name": "Quincy Jones", "email": "quincy.jones@example.com"},
    {"name": "Rachel Green", "email": "rachel.green@example.com"},
    {"name": "Samuel Jackson", "email": "samuel.jackson@example.com"},
    {"name": "Tina Turner", "email": "tina.turner@example.com"},
    {"name": "Ulysses Grant", "email": "ulysses.grant@example.com"},
    {"name": "Victoria Beckham", "email": "victoria.beckham@example.com"},
    {"name": "William Shakespeare", "email": "william.shakespeare@example.com"},
    {"name": "Xena Warrior", "email": "xena.warrior@example.com"},
    {"name": "Yoda Master", "email": "yoda.master@example.com"},
    {"name": "Zoe Saldana", "email": "zoe.saldana@example.com"},
]

def create_users():
    """Create users via API (which uses connection pooling)"""
    print("Creating users via FastAPI (using connection pooling)...")
    print("=" * 60)
    
    created_users = []
    start_time = time.time()
    
    for i, user_data in enumerate(USERS_DATA, 1):
        try:
            response = requests.post(
                f"{API_BASE_URL}/users/",
                json=user_data,
                timeout=10
            )
            
            if response.status_code == 201:
                user = response.json()
                created_users.append(user)
                print(f"[OK] Created user {i:2d}: {user['name']} (ID: {user['id']})")
            elif response.status_code == 409:
                print(f"[SKIP] User {i:2d}: {user_data['name']} already exists")
            else:
                print(f"[ERROR] Failed to create user {i:2d}: {user_data['name']} (Status: {response.status_code})")
                
        except Exception as e:
            print(f"[ERROR] Error creating user {i:2d}: {user_data['name']} - {e}")
    
    elapsed = time.time() - start_time
    print(f"\nCreated {len(created_users)} new users in {elapsed:.2f} seconds")
    return created_users

def fetch_all_users():
    """Fetch all users via API (which uses connection pooling)"""
    print("\nFetching all users via FastAPI (using connection pooling)...")
    print("=" * 60)
    
    try:
        start_time = time.time()
        response = requests.get(f"{API_BASE_URL}/users/", timeout=10)
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            users = response.json()
            print(f"[OK] Successfully fetched {len(users)} users in {elapsed:.3f} seconds")
            
            print(f"\nUser List (Total: {len(users)} users):")
            print("-" * 60)
            for user in users:
                print(f"ID: {user['id']:2d} | Name: {user['name']:<20} | Email: {user['email']}")
            
            return users
        else:
            print(f"[ERROR] Failed to fetch users (Status: {response.status_code})")
            return []
            
    except Exception as e:
        print(f"[ERROR] Error fetching users: {e}")
        return []

def test_concurrent_fetches():
    """Test concurrent fetches to demonstrate connection pooling"""
    print(f"\nTesting concurrent fetches (connection pool demonstration)...")
    print("=" * 60)
    
    import concurrent.futures
    import threading
    
    def fetch_users_worker(worker_id):
        """Worker function for concurrent fetches"""
        try:
            start_time = time.time()
            response = requests.get(f"{API_BASE_URL}/users/", timeout=10)
            elapsed = time.time() - start_time
            
            if response.status_code == 200:
                users = response.json()
                return {
                    'worker_id': worker_id,
                    'success': True,
                    'user_count': len(users),
                    'response_time': elapsed,
                    'thread_id': threading.get_ident()
                }
            else:
                return {
                    'worker_id': worker_id,
                    'success': False,
                    'error': f"HTTP {response.status_code}"
                }
        except Exception as e:
            return {
                'worker_id': worker_id,
                'success': False,
                'error': str(e)
            }
    
    # Run 10 concurrent requests
    num_workers = 10
    start_time = time.time()
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
        futures = [executor.submit(fetch_users_worker, i) for i in range(1, num_workers + 1)]
        results = [future.result() for future in concurrent.futures.as_completed(futures)]
    
    total_elapsed = time.time() - start_time
    
    # Analyze results
    successful = [r for r in results if r['success']]
    failed = [r for r in results if not r['success']]
    
    print(f"Concurrent fetch results:")
    print(f"- Total requests: {num_workers}")
    print(f"- Successful: {len(successful)}")
    print(f"- Failed: {len(failed)}")
    print(f"- Total time: {total_elapsed:.3f} seconds")
    
    if successful:
        avg_response_time = sum(r['response_time'] for r in successful) / len(successful)
        min_response_time = min(r['response_time'] for r in successful)
        max_response_time = max(r['response_time'] for r in successful)
        
        print(f"- Average response time: {avg_response_time:.3f} seconds")
        print(f"- Min response time: {min_response_time:.3f} seconds")
        print(f"- Max response time: {max_response_time:.3f} seconds")
        print(f"- Requests per second: {len(successful) / total_elapsed:.1f} RPS")
        
        # Show individual results
        print(f"\nIndividual request results:")
        for result in sorted(successful, key=lambda x: x['worker_id']):
            print(f"  Worker {result['worker_id']:2d}: {result['user_count']} users in {result['response_time']:.3f}s (Thread: {result['thread_id']})")
    
    if failed:
        print(f"\nFailed requests:")
        for result in failed:
            print(f"  Worker {result['worker_id']:2d}: {result['error']}")

def main():
    """Main function"""
    print("FastAPI Pool MVP - Database Population & Fetch Demo")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"API Base URL: {API_BASE_URL}")
    
    # Step 1: Create users
    created_users = create_users()
    
    # Step 2: Fetch all users
    all_users = fetch_all_users()
    
    # Step 3: Test concurrent fetches
    if len(all_users) >= 20:
        test_concurrent_fetches()
        print(f"\n[SUCCESS] Successfully demonstrated connection pooling with {len(all_users)} users!")
    else:
        print(f"\n[WARNING] Only {len(all_users)} users in database. Need at least 20 for full demo.")
    
    print("\n" + "=" * 60)
    print("Demo completed! The connection pool efficiently handled all database operations.")

if __name__ == "__main__":
    main()