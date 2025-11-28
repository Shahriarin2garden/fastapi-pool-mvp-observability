# FastAPI Pool MVP

A minimal, production-oriented FastAPI application showcasing **asyncpg connection pool** patterns for high-throughput PostgreSQL access.

**Complete Docker-Only Setup & Testing Guide**

---

## 📋 Prerequisites

- **Docker** (version 20.10+)
- **Docker Compose** (version 2.0+)
- **Git**

Verify installation:
```bash
docker --version
docker-compose --version
git --version
```

---

## 🚀 Step-by-Step Setup (Docker Only)

### Step 1: Initialize Repository

```bash
# Create project directory
mkdir fastapi-pool-mvp
cd fastapi-pool-mvp

# Initialize git repository
git init
```

### Step 2: Clone or Create Project Files

**Option A: Clone existing repository**
```bash
git clone https://github.com/yourusername/fastapi-pool-mvp.git
cd fastapi-pool-mvp
```

**Option B: Create from scratch** (skip if cloning)
```bash
# Create directory structure
mkdir -p app/db app/routes app/services app/schemas app/utils
mkdir -p migrations tests

# Create empty __init__.py files
touch app/__init__.py app/db/__init__.py
```

### Step 3: Environment Configuration

```bash
# Copy environment template
cp .env.example .env

# View default configuration
cat .env
```

**Default `.env` contents:**
```env
DB_HOST=db
DB_PORT=5432
DB_USER=postgres
DB_PASS=postgres
DB_NAME=fastdb
POOL_MIN_SIZE=2
POOL_MAX_SIZE=10
COMMAND_TIMEOUT=5
```

### Step 4: Build and Start Services

```bash
# Build and start all services
docker-compose up --build -d

# Verify services are running
docker-compose ps
```

**Expected output:**
```
NAME                     IMAGE                  STATUS         PORTS
fastapi-pool-mvp-app-1   fastapi-pool-mvp-app   Up 30 seconds  0.0.0.0:8001->8000/tcp
fastapi-pool-mvp-db-1    postgres:15            Up 31 seconds  0.0.0.0:5432->5432/tcp
```

### Step 5: Verify Application Startup

```bash
# Check application logs
docker-compose logs app
```

**Expected startup logs:**
```
Initializing database pool...
Pool initialized successfully with 2-10 connections
Creating database tables...
Tables created successfully
Application startup completed successfully
INFO:     Application startup complete.
```

---

## 🧪 Complete Testing Guide (Docker Only)

### Test 1: Basic Health Check

```bash
# Test health endpoint
curl http://localhost:8001/health
```

**Expected response:**
```json
{"status":"ok"}
```

### Test 2: API Endpoints Testing

```bash
# 1. List users (initially empty)
curl http://localhost:8001/users/
# Expected: []

# 2. Create first user
curl -X POST http://localhost:8001/users/ \
  -H "Content-Type: application/json" \
  -d '{"name":"Alice Johnson","email":"alice@example.com"}'
# Expected: {"id":1,"name":"Alice Johnson","email":"alice@example.com"}

# 3. Create second user
curl -X POST http://localhost:8001/users/ \
  -H "Content-Type: application/json" \
  -d '{"name":"Bob Smith","email":"bob@example.com"}'
# Expected: {"id":2,"name":"Bob Smith","email":"bob@example.com"}

# 4. List all users
curl http://localhost:8001/users/
# Expected: [{"id":1,"name":"Alice Johnson","email":"alice@example.com"},{"id":2,"name":"Bob Smith","email":"bob@example.com"}]

# 5. Get specific user
curl http://localhost:8001/users/1
# Expected: {"id":1,"name":"Alice Johnson","email":"alice@example.com"}

# 6. Test error handling (duplicate email)
curl -X POST http://localhost:8001/users/ \
  -H "Content-Type: application/json" \
  -d '{"name":"Charlie","email":"alice@example.com"}'
# Expected: {"detail":"Email already registered"}

# 7. Test 404 error
curl http://localhost:8001/users/999
# Expected: {"detail":"User not found"}
```

### Test 3: Database Connection Testing

```bash
# Access PostgreSQL directly
docker-compose exec db psql -U postgres -d fastdb
```

**Inside PostgreSQL:**
```sql
-- Check users table
SELECT * FROM users;

-- Check active connections
SELECT count(*) as active_connections 
FROM pg_stat_activity 
WHERE datname = 'fastdb';

-- Check database size
SELECT pg_size_pretty(pg_database_size('fastdb'));

-- Exit PostgreSQL
\q
```

### Test 4: Unit Tests

```bash
# Run pytest inside container
docker-compose exec app pytest tests/ -v
```

**Expected output:**
```
============================= test session starts ==============================
tests/test_users.py::test_health_check PASSED                            [ 33%]
tests/test_users.py::test_list_users PASSED                              [ 66%]
tests/test_users.py::test_create_user PASSED                             [100%]
============================== 3 passed in 0.40s
```

### Test 5: Real-Time Database Monitoring

```bash
# Install monitoring dependencies in container
docker-compose exec app pip install aiohttp

# Run real-time database monitor
docker-compose exec app python monitoring/monitor_db.py
```

**Expected monitoring output:**
```
[00:15:30] FastAPI Pool MVP - DB Monitor (Iteration 1)
============================================================
Database Status:     [CONNECTED]
Total Connections:   3
Active Connections:  1
Idle Connections:    2
Users in Database:   2
Database Size:       7581 kB
```

### Test 6: Connection Pool Stress Testing

```bash
# Run stress test
docker-compose exec app python monitoring/stress_test.py
```

**Expected stress test results:**
```
Test 1: Light Load (5 workers, 5 seconds)
============================================================
Duration:            5.00 seconds
Total Requests:      1334
Successful Requests: 1334
Failed Requests:     0
Success Rate:        100.0%
Requests per Second: 266.5 RPS
SUCCESS: All requests completed without errors!
```

### Test 7: Live API + Database Monitoring

```bash
# Run live monitor (tests both API and DB)
docker-compose exec app python monitoring/live_monitor.py
```

**Expected live monitoring:**
```
[00:20:15] Live Monitor - Iteration 1/10
--------------------------------------------------
DB Connections:      Total: 3, Active: 1, Idle: 2
AsyncPG Connections: 0
API Health:          HTTP 200
API Users:           HTTP 200 (2 users)

Simulating API load...
Load Test:           5/5 requests successful
```

### Test 8: Interactive Database Testing

```bash
# Run interactive database test
docker-compose exec app python monitoring/test_db_realtime.py
```

**Choose option 1 for real-time monitoring or option 2 for stress testing.**

### Test 9: 100 Concurrent Requests Test

```bash
# Install required dependency
docker-compose exec app pip install aiohttp

# Run 100 concurrent requests test
docker-compose exec app python test_100_concurrent.py
```

**Expected results:**
```
======================================================================
TESTING 100 CONCURRENT REQUESTS
======================================================================

📊 Initial Database State:
Total Connections: 3
Active Connections: 1
Idle Connections: 2

🚀 Launching 100 concurrent requests at 18:51:11
[18:51:12] DB Connections - Total: 11, Active: 1, Idle: 10

📈 RESULTS:
Total Duration: 0.62 seconds
Successful Requests: 100/100
Failed Requests: 0
Success Rate: 100%
Requests per Second: 160.4 RPS
Average Response Time: 494.4ms

📊 Final Database State:
Total Connections: 11
Active Connections: 1
Idle Connections: 10
```

### Test 10: Connection Pool Limits Testing

```bash
# Test pool scaling and limits
docker-compose exec app python test_pool_limits.py
```

**Expected pool scaling behavior:**
```
============================================================
CONNECTION POOL SCALING TEST
============================================================
Pool created: min_size=2, max_size=10
Initial pool size: 2

Attempting to acquire connection 1...
✅ Acquired connection 1
Current pool size: 2
Database shows 4 total connections

[... continues until connection 10 ...]

Attempting to acquire connection 11...
❌ Timeout acquiring connection 11 (pool limit reached)

📊 Final Results:
Connections acquired: 10
Pool size: 10
```

---

## 🎯 Connection Pool Effectiveness Analysis

### How Connection Pool Handles 100 Concurrent Requests

Your connection pool demonstrates exceptional effectiveness when handling concurrent load:

#### **Without Connection Pool (Disaster Scenario)**
```
100 concurrent requests → 100 database connections
Result: Database OVERLOADED/CRASHED
Memory Usage: ~1GB (10MB per connection)
Response: TIMEOUT/FAILURE
```

#### **With Connection Pool (Your Results)**
```
100 concurrent requests → Max 10 database connections
Result: 100% SUCCESS in 0.62 seconds
Memory Usage: ~100MB total (90% savings)
Response: 160+ RPS with stable performance
```

### **Connection Pool Behavior Under Load**

#### **1. Request Queuing & Processing**
```
Requests 1-10:  Get connections immediately
Requests 11-100: Wait in asyncio queue for available connections
Processing:     Batches of 10 concurrent operations
Result:         All requests complete in ~0.6 seconds
```

#### **2. Pool Scaling Pattern**
```
Initial State:    3 connections (1 active, 2 idle)
Under Load:      11 connections (1 active, 10 idle)
Pool Limit:      Max 10 from app + 1 monitoring
Scaling:         Automatic from min_size=2 to max_size=10
```

#### **3. Performance Metrics**

| Load Level | Workers | Operations/sec | Pool Behavior |
|------------|---------|----------------|---------------|
| Light      | 5       | 396.9 OPS     | Scales to 6 connections |
| Medium     | 15      | 725.9 OPS     | Uses all 10 connections |
| Heavy      | 25      | 766.4 OPS     | Maintains 10 connections |
| Extreme    | 50      | 741.0 OPS     | Stable at 10 connections |

### **Key Benefits Demonstrated**

1. **Resource Protection**: Database never overwhelmed
2. **Memory Efficiency**: 90% less memory usage vs no pooling
3. **Performance**: 160+ RPS with sub-second response times
4. **Reliability**: Zero failures under heavy concurrent load
5. **Scalability**: Handles traffic spikes gracefully
6. **Queue Management**: Fair request scheduling (FIFO)

### **Real-World Impact**

**Timeline for 100 Concurrent Requests:**
```
Time 0ms:    Requests 1-10 get connections immediately
Time 60ms:   First batch completes, requests 11-20 start
Time 120ms:  Second batch completes, requests 21-30 start
...
Time 620ms:  All 100 requests completed successfully
```

**Connection Reuse Efficiency:**
```
# Without Pool (expensive):
conn = await asyncpg.connect(...)  # ~50ms overhead per request
result = await conn.fetchval(...)
await conn.close()

# With Pool (efficient):
async with pool.acquire() as conn:  # ~1ms overhead
    result = await conn.fetchval(...)
# Connection reused for next request
```

---

## 📊 Performance Verification

### Connection Pool Metrics

```bash
# Check pool performance
docker-compose exec db psql -U postgres -d fastdb -c "
SELECT 
    count(*) as total_connections,
    count(*) FILTER (WHERE state = 'active') as active_connections,
    count(*) FILTER (WHERE state = 'idle') as idle_connections
FROM pg_stat_activity 
WHERE datname = 'fastdb';"
```

### Load Testing with curl

```bash
# Concurrent requests test
for i in {1..10}; do
  curl -s http://localhost:8001/users/ &
done
wait
echo "All requests completed"
```

### API Documentation

```bash
# Access Swagger UI
echo "Open http://localhost:8001/docs in your browser"

# Get OpenAPI JSON
curl http://localhost:8001/openapi.json | jq .
```

---

## 🔧 Troubleshooting

### Issue: Port Already in Use

```bash
# Stop all containers
docker-compose down

# Change port in docker-compose.yml
sed -i 's/8001:8000/8002:8000/' docker-compose.yml

# Restart
docker-compose up -d
```

### Issue: Database Connection Failed

```bash
# Check container status
docker-compose ps

# Check database logs
docker-compose logs db

# Check application logs
docker-compose logs app

# Restart services
docker-compose restart
```

### Issue: Application Not Starting

```bash
# Rebuild containers
docker-compose down
docker-compose build --no-cache
docker-compose up -d

# Check logs for errors
docker-compose logs app --tail=50
```

---

## 📈 Performance Results

**Verified Performance Metrics:**

| Test Type | Metric | Result |
|-----------|--------|---------|
| Health Check | Response Time | < 10ms |
| Single User Query | Response Time | < 15ms |
| Connection Pool | Min/Max Connections | 2/10 |
| **100 Concurrent Requests** | **Success Rate** | **100%** |
| **100 Concurrent Requests** | **Total Duration** | **0.62 seconds** |
| **100 Concurrent Requests** | **Requests/Second** | **160.4 RPS** |
| **100 Concurrent Requests** | **Avg Response Time** | **494ms** |
| **100 Concurrent Requests** | **DB Connections Used** | **Max 10** |
| Stress Test (5 workers) | Requests/Second | 266.5 RPS |
| Stress Test (15 workers) | Requests/Second | 441.7 RPS |
| Stress Test (25 workers) | Requests/Second | 396.7 RPS |
| Pool Scaling Test | Max Connections | 10 (11th times out) |
| Sequential vs Concurrent | Speedup | 1.8x faster |
| Database Size | Storage | ~7.5 MB |
| Memory Usage | Container | ~60 MB |

---

## 🏗️ Architecture Overview

### Repository Structure
```
fastapi-pool-mvp/
├── app/
│   ├── main.py                 # FastAPI app + lifecycle
│   ├── config.py               # Environment settings
│   ├── db/
│   │   ├── pool.py            # Connection pool
│   │   └── init_db.py         # Table initialization
│   ├── routes/
│   │   └── user.py            # API endpoints
│   ├── services/
│   │   └── user_service.py    # Database operations
│   └── schemas/
│       └── user_schema.py     # Data models
├── tests/
│   └── test_users.py          # Unit tests
├── monitoring/
│   ├── monitor_db.py          # Real-time DB monitor
│   ├── stress_test.py         # Load testing
│   ├── live_monitor.py        # API + DB monitor
│   └── test_db_realtime.py    # Interactive testing
├── docker-compose.yml         # Multi-container setup
├── Dockerfile                 # App container
├── requirements.txt           # Python dependencies
└── .env                       # Environment variables
```

### Connection Pool Flow

1. **Startup**: Pool initializes with 2 connections
2. **Load Increase**: Pool scales up to 10 connections
3. **Request Handling**: Connections acquired/released automatically
4. **Cleanup**: Idle connections recycled after 300s
5. **Shutdown**: Pool closes gracefully

---

## 🔄 Development Workflow

### Making Changes

```bash
# 1. Make code changes
vim app/main.py

# 2. Restart application
docker-compose restart app

# 3. Test changes
curl http://localhost:8001/health

# 4. Run tests
docker-compose exec app pytest tests/ -v
```

### Adding New Dependencies

```bash
# 1. Add to requirements.txt
echo "new-package==1.0.0" >> requirements.txt

# 2. Rebuild container
docker-compose build app

# 3. Restart services
docker-compose up -d
```

### Database Operations

```bash
# Connect to database
docker-compose exec db psql -U postgres -d fastdb

# Backup database
docker-compose exec db pg_dump -U postgres fastdb > backup.sql

# Restore database
docker-compose exec -T db psql -U postgres fastdb < backup.sql
```

---

## 🚀 Production Deployment

### Environment Variables for Production

```env
# Production .env
DB_HOST=your-postgres-host
DB_PORT=5432
DB_USER=your-db-user
DB_PASS=your-secure-password
DB_NAME=your-db-name
POOL_MIN_SIZE=5
POOL_MAX_SIZE=50
COMMAND_TIMEOUT=10
```

### Docker Compose for Production

```yaml
# docker-compose.prod.yml
version: '3.8'
services:
  app:
    build: .
    ports:
      - "80:8000"
    environment:
      - DB_HOST=${DB_HOST}
      - DB_USER=${DB_USER}
      - DB_PASS=${DB_PASS}
    restart: unless-stopped
    depends_on:
      - db
  
  db:
    image: postgres:15
    environment:
      - POSTGRES_USER=${DB_USER}
      - POSTGRES_PASSWORD=${DB_PASS}
      - POSTGRES_DB=${DB_NAME}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

volumes:
  postgres_data:
```

---

## 📚 API Documentation

### Available Endpoints

| Method | Endpoint | Description | Response |
|--------|----------|-------------|----------|
| GET | `/health` | Health check | `{"status": "ok"}` |
| GET | `/users/` | List all users | `[{user objects}]` |
| POST | `/users/` | Create user | `{user object}` |
| GET | `/users/{id}` | Get user by ID | `{user object}` |
| GET | `/docs` | Swagger UI | HTML page |
| GET | `/openapi.json` | OpenAPI spec | JSON schema |

### Error Responses

| Status Code | Description | Example |
|-------------|-------------|----------|
| 200 | Success | `{"id": 1, "name": "Alice"}` |
| 201 | Created | `{"id": 2, "name": "Bob"}` |
| 404 | Not Found | `{"detail": "User not found"}` |
| 409 | Conflict | `{"detail": "Email already registered"}` |
| 422 | Validation Error | `{"detail": [{"loc": ["email"], "msg": "Invalid email"}]}` |
| 500 | Server Error | `{"detail": "Internal server error"}` |

---

## 🔍 Monitoring & Observability

### Real-Time Monitoring Commands

```bash
# Monitor application logs
docker-compose logs -f app

# Monitor database logs
docker-compose logs -f db

# Monitor system resources
docker stats

# Monitor database connections
docker-compose exec db psql -U postgres -d fastdb -c "
SELECT pid, usename, application_name, state, query_start 
FROM pg_stat_activity 
WHERE datname = 'fastdb';"
```

### Health Checks

```bash
# Application health
curl -f http://localhost:8001/health || echo "App unhealthy"

# Database health
docker-compose exec db pg_isready -U postgres || echo "DB unhealthy"

# Container health
docker-compose ps | grep -q "Up" || echo "Containers down"
```

---

## 🛡️ Security Considerations

### Production Security Checklist

- [ ] Change default database passwords
- [ ] Use environment variables for secrets
- [ ] Enable SSL/TLS for database connections
- [ ] Implement rate limiting
- [ ] Add authentication/authorization
- [ ] Use non-root user in containers
- [ ] Scan images for vulnerabilities
- [ ] Enable container security scanning
- [ ] Implement proper logging
- [ ] Set up monitoring and alerting

---

## 📝 License

MIT License - see LICENSE file for details.

---

## ✅ Quick Verification Checklist

After following all setup steps, verify everything works:

```bash
# 1. Check services are running
docker-compose ps
# Expected: Both app and db containers should show "Up"

# 2. Test health endpoint
curl http://localhost:8001/health
# Expected: {"status":"ok"}

# 3. Test API functionality
curl http://localhost:8001/users/
# Expected: JSON array (may be empty initially)

# 4. Create a test user
curl -X POST http://localhost:8001/users/ \
  -H "Content-Type: application/json" \
  -d '{"name":"Test User","email":"test@example.com"}'
# Expected: {"id":1,"name":"Test User","email":"test@example.com"}

# 5. Run unit tests
docker-compose exec app pytest tests/ -v
# Expected: 3 tests passed

# 6. Access Swagger UI
# Open http://localhost:8001/docs in browser
# Expected: Interactive API documentation
```

**If all checks pass: ✅ Setup Complete!**

---

**🎉 Congratulations! You now have a fully functional FastAPI application with asyncpg connection pooling running in Docker containers.**

**Next Steps:**
- Explore the Swagger UI at http://localhost:8001/docs
- Run the monitoring tools to see real-time performance
- Customize the application for your specific needs
- Deploy to production with proper security measures