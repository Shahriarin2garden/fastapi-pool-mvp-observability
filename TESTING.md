# Testing Guide

All tests run inside the Docker container against the live application and database.

## Quick Reference

```bash
# Start services
docker compose up --build -d

# Unit + integration tests
docker compose exec app pytest tests/ -v

# 100 concurrent requests benchmark
docker compose exec app python load_test.py

# Connection pool limit verification
docker compose exec app python test_pool_limits.py

# Multi-level stress test (5/15/25 workers)
docker compose exec app python monitoring/stress_test.py

# Live API + DB monitor (10 iterations)
docker compose exec app python monitoring/live_monitor.py

# Real-time DB connection monitor (continuous)
docker compose exec app python monitoring/monitor_db.py

# Windows: 50 concurrent curl requests
test_concurrent_curl.bat
```

## Test Matrix

| Test | Type | Duration | What It Validates |
|------|------|----------|-------------------|
| `pytest tests/ -v` | Integration | ~1s | Health check, user CRUD, duplicate email rejection |
| `load_test.py` | Load | ~1s | 100 concurrent requests, latency percentiles, RPS |
| `test_pool_limits.py` | Boundary | ~15s | Pool max enforced, 11th connection times out |
| `stress_test.py` | Stress | ~25s | Sustained throughput at 5/15/25 workers |
| `live_monitor.py` | Health | ~20s | API endpoints + DB connections, periodic load |
| `monitor_db.py` | Monitor | Continuous | Connection counts, pool size, DB size |

## Expected Benchmarks

| Metric | Expected |
|--------|----------|
| 100 concurrent success rate | 100% |
| Throughput (100 req) | 160–335 RPS |
| Latency p50 | ~180ms |
| Latency p99 | ~300ms |
| Max DB connections under load | 10 (pool max) |
| 11th connection | Timeout |

## CI/CD Integration

```yaml
# GitHub Actions
- name: Run Tests
  run: |
    docker compose up -d
    docker compose exec -T app pytest tests/ -v
    docker compose exec -T app python load_test.py
```
