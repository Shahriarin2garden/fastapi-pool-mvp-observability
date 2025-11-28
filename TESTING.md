# Testing Guide

## Quick Start Testing

### 1. Basic Health Check
```bash
curl http://localhost:8001/health
```

### 2. Run All Tests
```bash
docker-compose exec app pytest tests/ -v
```

## Load Testing

### Python Load Tests

#### Test 1: 100 Concurrent Requests (Detailed)
```bash
docker-compose exec app python test_100_concurrent.py
```

**Expected Results:**
- Success Rate: 100%
- Duration: ~0.3-0.6 seconds
- RPS: 160-280
- DB Connections: Max 11 (10 pool + 1 monitoring)

#### Test 2: Clean Load Test
```bash
docker-compose exec app python load_test.py
```

**Expected Results:**
- Success: 100/100
- Total Time: ~0.3 seconds
- RPS: 300+
- Latency p50: ~180ms
- Latency p99: ~300ms

#### Test 3: Pool Limits Test
```bash
docker-compose exec app python test_pool_limits.py
```

**Expected Results:**
- Connections 1-10: Acquired successfully
- Connection 11: Timeout (pool limit enforced)

### Windows Batch Test

```bash
test_concurrent_curl.bat
```

**Expected Results:**
- 50 concurrent requests completed
- DB connections stay within pool limits
- All requests successful

## Postman Testing

### Setup
1. Create request: `GET http://localhost:8001/users/`
2. Save to collection
3. Run Collection Runner with 100 iterations, 0ms delay

### Expected Results
- 100/100 requests: 200 OK
- Average response: ~37ms
- Total duration: ~18 seconds (sequential)
- DB connections: Max 11

## Database Monitoring

### Check Connection Pool State
```bash
docker-compose exec db psql -U postgres -d fastdb -c "
SELECT 
    count(*) as total_connections,
    count(*) FILTER (WHERE state = 'active') as active_connections,
    count(*) FILTER (WHERE state = 'idle') as idle_connections
FROM pg_stat_activity 
WHERE datname = 'fastdb';"
```

### Real-Time Monitoring
```bash
docker-compose exec app python monitoring/monitor_db.py
```

## Performance Benchmarks

| Test Type | Requests | Duration | RPS | Success Rate | DB Connections |
|-----------|----------|----------|-----|--------------|----------------|
| Python Concurrent | 100 | 0.36s | 280.5 | 100% | 11 |
| Load Test | 100 | 0.30s | 335.6 | 100% | 11 |
| Postman Sequential | 100 | 18.5s | 5.4 | 100% | 11 |
| Batch Script | 50 | ~3s | ~17 | 100% | 11 |

## Troubleshooting

### Issue: Tests Fail
```bash
# Check if app is running
docker-compose ps

# Restart services
docker-compose restart app

# Check logs
docker-compose logs app --tail=50
```

### Issue: Connection Errors
```bash
# Verify database is accessible
docker-compose exec db pg_isready -U postgres

# Check network
docker-compose exec app ping db
```

## CI/CD Integration

### GitHub Actions Example
```yaml
- name: Run Tests
  run: |
    docker-compose up -d
    docker-compose exec -T app pytest tests/ -v
    docker-compose exec -T app python load_test.py
```

## Test Coverage

- ✅ Health endpoints
- ✅ CRUD operations
- ✅ Connection pool limits
- ✅ Concurrent load handling
- ✅ Error handling
- ✅ Database connection management
- ✅ Performance benchmarks
