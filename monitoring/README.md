# Monitoring Tools

Real-time monitoring and load testing tools for the FastAPI connection pool.

All tools run inside the Docker container:

```bash
# Real-time DB connection monitor (runs continuously, Ctrl+C to stop)
docker compose exec app python monitoring/monitor_db.py

# Multi-level stress test (5/15/25 workers, ~25s total)
docker compose exec app python monitoring/stress_test.py

# Live API + DB health monitor (10 iterations, ~20s)
docker compose exec app python monitoring/live_monitor.py

# Interactive testing (choose monitoring or stress test mode)
docker compose exec app python monitoring/test_db_realtime.py
```

## Prometheus + Grafana

Prometheus scrapes `/metrics` every 5s. Grafana dashboard is auto-provisioned at `http://localhost:3000` (admin/admin).

See the main [README](../README.md#observability) for metric definitions and dashboard panel descriptions.
