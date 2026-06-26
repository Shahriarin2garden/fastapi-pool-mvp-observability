<p align="center">
  <img src="https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI" />
  <img src="https://img.shields.io/badge/PostgreSQL-4169E1?style=for-the-badge&logo=postgresql&logoColor=white" alt="PostgreSQL" />
  <img src="https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white" alt="Docker" />
  <img src="https://img.shields.io/badge/Prometheus-E6522C?style=for-the-badge&logo=prometheus&logoColor=white" alt="Prometheus" />
  <img src="https://img.shields.io/badge/Grafana-F46800?style=for-the-badge&logo=grafana&logoColor=white" alt="Grafana" />
  <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python" />
</p>

<h1 align="center">FastAPI Pool MVP</h1>

<p align="center">
  <strong>Production-grade async connection pooling for PostgreSQL — benchmarked, monitored, containerized.</strong>
</p>

<p align="center">
  <a href="#architecture">Architecture</a> &bull;
  <a href="#key-results">Key Results</a> &bull;
  <a href="#quick-start">Quick Start</a> &bull;
  <a href="#testing">Testing</a> &bull;
  <a href="#observability">Observability</a> &bull;
  <a href="#api-reference">API Reference</a>
</p>

---

## Why This Project Exists

Most tutorials show database connections opened and closed per request. That works for 10 users. At 100+ concurrent requests, the database collapses under connection overhead.

This project demonstrates a **production-ready solution**: an `asyncpg` connection pool that caps database connections at a configurable maximum, queues excess requests transparently, and scales from 2 idle connections to 10 under load — all proven through automated load tests.

**The result:** 100 concurrent requests complete in 0.62 seconds with zero failures, using only 10 database connections instead of 100.

---

## Architecture

```
                    ┌─────────────────────────────────────────────────┐
                    │                 Docker Compose                   │
                    │                                                  │
  Clients ──────── │ ┌──────────┐    ┌──────────┐    ┌─────────────┐ │
  (HTTP :8001)     │ │ FastAPI  │───▶│ asyncpg  │───▶│ PostgreSQL  │ │
                    │ │ Uvicorn  │    │   Pool   │    │   15        │ │
                    │ │          │    │ (2─10)   │    │             │ │
                    │ └────┬─────┘    └──────────┘    └─────────────┘ │
                    │      │                                          │
                    │      │ /metrics                                 │
                    │      ▼                                          │
                    │ ┌──────────┐    ┌─────────────┐                 │
                    │ │Prometheus│───▶│  Grafana     │                 │
                    │ │  (:9090) │    │  (:3000)     │                 │
                    │ └──────────┘    └─────────────┘                 │
                    └─────────────────────────────────────────────────┘
```

### Project Structure

```
fastapi-pool-mvp/
├── app/
│   ├── main.py                  # FastAPI app with async lifespan management
│   ├── config.py                # Pydantic settings (env-driven)
│   ├── db/
│   │   ├── pool.py              # asyncpg pool init/close lifecycle
│   │   └── init_db.py           # DDL execution on startup
│   ├── routes/
│   │   └── user.py              # REST endpoints with proper HTTP status codes
│   ├── services/
│   │   └── user_service.py      # Data access layer with Prometheus instrumentation
│   ├── schemas/
│   │   └── user_schema.py       # Pydantic request/response models
│   └── monitoring/
│       └── metrics.py           # Custom Prometheus gauges, histograms, counters
├── tests/
│   └── test_users.py            # Integration tests (health, CRUD, idempotency)
├── monitoring/
│   ├── monitor_db.py            # Real-time connection pool monitor
│   ├── stress_test.py           # Multi-level load testing (5→50 workers)
│   ├── live_monitor.py          # Combined API + DB health monitor
│   └── test_db_realtime.py      # Interactive pool testing tool
├── prometheus/
│   └── prometheus.yml           # Scrape config targeting FastAPI /metrics
├── grafana/
│   └── provisioning/            # Auto-provisioned datasource + dashboards
│       ├── datasources/
│       └── dashboards/
│           └── fastapi-dashboard.json   # 6-panel monitoring dashboard
├── docker-compose.yml           # 4-service stack (app, db, prometheus, grafana)
├── Dockerfile                   # Python 3.11-slim production image
├── requirements.txt             # Pinned dependencies
├── load_test.py                 # Standalone 100-request concurrent benchmark
├── verify_setup.bat             # Windows one-click verification script
└── test_concurrent_curl.bat     # 50-request curl concurrency test
```

### Design Decisions

| Decision | Rationale |
|----------|-----------|
| **asyncpg** over SQLAlchemy async | Raw asyncpg gives ~3x throughput for simple CRUD; no ORM overhead for a connection-pool demo |
| **Pydantic v1 BaseSettings** | Direct `.env` binding, zero boilerplate config |
| **Lifespan context manager** | Clean pool init/teardown — no deprecated `on_event` decorators |
| **Prometheus + Grafana** | Industry-standard observability; auto-provisioned so `docker compose up` gives a working dashboard |
| **No ORM migrations** | `CREATE TABLE IF NOT EXISTS` — intentionally simple for a pool-focused demo |

---

<a name="key-results"></a>
## Key Results

### Connection Pool Under Load

<table>
<tr>
<td width="50%">

**Without Connection Pool**
```
100 concurrent requests
→ 100 database connections opened
→ ~1 GB memory (10 MB/conn)
→ PostgreSQL max_connections exceeded
→ CRASH
```

</td>
<td width="50%">

**With asyncpg Pool (this project)**
```
100 concurrent requests
→ Max 10 database connections
→ ~100 MB memory (90% savings)
→ Requests queued via asyncio
→ 100% SUCCESS in 0.62s
```

</td>
</tr>
</table>

### Benchmark Results

| Metric | Value |
|--------|-------|
| Concurrent requests handled | **100/100** (0% failure) |
| Total duration | **0.62s** |
| Throughput | **160+ RPS** |
| Avg response time | **494ms** |
| Peak DB connections | **10** (pool max) |
| Pool scale-up | 2 → 10 (automatic) |
| 11th connection attempt | Timeout (limit enforced) |
| Container memory | ~60 MB |

### Stress Test Scaling

| Workers | Operations/sec | Pool Behavior |
|---------|---------------|---------------|
| 5 | 396.9 | Scales to 6 connections |
| 15 | 725.9 | Saturates at 10 connections |
| 25 | 766.4 | Maintains 10 connections |
| 50 | 741.0 | Stable — queue absorbs overflow |

The pool hits peak throughput at 15–25 workers. Beyond that, performance plateaus (not degrades) — exactly the behavior a production pool should exhibit.

---

<a name="quick-start"></a>
## Quick Start

### Prerequisites

- Docker 20.10+
- Docker Compose v2+

### 1. Clone and configure

```bash
git clone https://github.com/Shahriarin2garden/fastapi-pool-mvp.git
cd fastapi-pool-mvp
cp .env.example .env
```

### 2. Start all services

```bash
docker compose up --build -d
```

This launches four containers:

| Service | Port | Purpose |
|---------|------|---------|
| **app** | `localhost:8001` | FastAPI + Uvicorn (hot-reload) |
| **db** | `localhost:5432` | PostgreSQL 15 |
| **prometheus** | `localhost:9090` | Metrics collection (5s scrape) |
| **grafana** | `localhost:3000` | Dashboards (admin/admin) |

### 3. Verify

```bash
# Health check
curl http://localhost:8001/health
# → {"status":"ok"}

# Create a user
curl -X POST http://localhost:8001/users/ \
  -H "Content-Type: application/json" \
  -d '{"name":"Alice","email":"alice@example.com"}'
# → {"id":1,"name":"Alice","email":"alice@example.com"}

# Swagger UI
open http://localhost:8001/docs
```

---

<a name="testing"></a>
## Testing

### Unit / Integration Tests

```bash
docker compose exec app pytest tests/ -v
```

```
tests/test_users.py::test_health_check PASSED
tests/test_users.py::test_list_users PASSED
tests/test_users.py::test_create_user PASSED
============================== 3 passed ==============================
```

Tests run inside the container against the live app and database — no mocks.

### Load Test — 100 Concurrent Requests

```bash
docker compose exec app python load_test.py
```

Fires 100 requests simultaneously via `aiohttp` with `asyncio.gather`, reports latency percentiles (p50/p90/p99) and database connection state before and after.

### Connection Pool Limit Test

```bash
docker compose exec app python test_pool_limits.py
```

Acquires connections one at a time up to the pool max (10), then verifies the 11th attempt times out — proving the pool enforces its ceiling.

### Stress Test (Multi-Level)

```bash
docker compose exec app python monitoring/stress_test.py
```

Runs three progressive load levels (5 → 15 → 25 workers) to show how the pool scales up and stabilizes.

### All Tests at a Glance

| Test | Command | What It Proves |
|------|---------|---------------|
| Health + CRUD | `pytest tests/ -v` | Endpoints work, schema validation, duplicate-email rejection |
| 100 concurrent | `python load_test.py` | Pool handles burst load with 0% failure |
| Pool limits | `python test_pool_limits.py` | Max connections enforced, 11th times out |
| Stress test | `python monitoring/stress_test.py` | Sustained load across escalating worker counts |
| Live monitor | `python monitoring/live_monitor.py` | API + DB health checked over 10 iterations |
| DB monitor | `python monitoring/monitor_db.py` | Real-time connection/pool/size tracking |

---

<a name="observability"></a>
## Observability

### Prometheus Metrics

The app exposes `/metrics` with both auto-instrumented HTTP metrics (via `prometheus-fastapi-instrumentator`) and custom pool metrics:

| Metric | Type | Description |
|--------|------|-------------|
| `http_requests_total` | Counter | Total HTTP requests by method/handler/status |
| `http_request_duration_seconds` | Histogram | Request latency distribution |
| `db_pool_size` | Gauge | Current number of connections in pool |
| `db_pool_max_size` | Gauge | Configured pool maximum |
| `db_query_duration_seconds` | Histogram | SQL query execution time |
| `db_connection_acquire_duration_seconds` | Histogram | Time to acquire a connection from pool |
| `db_query_errors_total` | Counter | Failed queries |
| `db_connection_errors_total` | Counter | Failed connection acquisitions |

### Grafana Dashboard

Auto-provisioned at `http://localhost:3000` (login: admin/admin). Six panels:

1. **Request Rate** — `rate(http_requests_total[1m])` by method/handler
2. **Request Latency (p95)** — `histogram_quantile(0.95, ...)`
3. **Connection Pool Size** — current vs. max
4. **Query Duration** — SQL execution time histogram
5. **Connection Acquire Time** — pool wait time
6. **Error Rates** — query + connection failures

### Direct Database Monitoring

```bash
# Active connection snapshot
docker compose exec db psql -U postgres -d fastdb -c "
  SELECT count(*) AS total,
         count(*) FILTER (WHERE state='active') AS active,
         count(*) FILTER (WHERE state='idle') AS idle
  FROM pg_stat_activity WHERE datname='fastdb';"
```

---

<a name="api-reference"></a>
## API Reference

| Method | Endpoint | Status | Description |
|--------|----------|--------|-------------|
| `GET` | `/health` | 200 | Health check |
| `GET` | `/users/` | 200 | List all users |
| `POST` | `/users/` | 201 | Create user (unique email enforced) |
| `GET` | `/users/{id}` | 200 | Get user by ID |
| `GET` | `/docs` | 200 | Swagger UI |
| `GET` | `/metrics` | 200 | Prometheus metrics |

### Error Responses

| Status | Meaning | Example |
|--------|---------|---------|
| 404 | Resource not found | `{"detail": "User not found"}` |
| 409 | Unique constraint violation | `{"detail": "Email already registered"}` |
| 422 | Validation error | Pydantic field-level errors |

---

## How the Pool Works

```
Time 0ms     Requests 1–10 get connections immediately (pool scales 2→10)
Time ~60ms   First batch completes → connections returned → Requests 11–20 start
Time ~120ms  Second batch completes → Requests 21–30 start
  ...
Time ~620ms  All 100 requests completed. Zero failures.
```

Connection reuse eliminates the ~50ms overhead of establishing a new TCP + auth handshake per request:

```python
# Without pool — 50ms overhead per request
conn = await asyncpg.connect(...)
result = await conn.fetchval(...)
await conn.close()

# With pool — <1ms overhead
async with pool.acquire() as conn:
    result = await conn.fetchval(...)
# Connection returned to pool, reused immediately
```

### Pool Configuration

Controlled via environment variables (`.env`):

| Variable | Default | Description |
|----------|---------|-------------|
| `POOL_MIN_SIZE` | 2 | Minimum idle connections maintained |
| `POOL_MAX_SIZE` | 10 | Maximum connections allowed |
| `COMMAND_TIMEOUT` | 5 | Query timeout (seconds) |
| `max_inactive_connection_lifetime` | 300s | Idle connections recycled after 5 min |

---

## Development

```bash
# Hot-reload is enabled — edit code, app restarts automatically
docker compose logs -f app

# Run tests after changes
docker compose exec app pytest tests/ -v

# Rebuild after dependency changes
docker compose build app && docker compose up -d app

# Database shell
docker compose exec db psql -U postgres -d fastdb
```

---

## Production Considerations

```env
# Recommended production overrides
POOL_MIN_SIZE=5
POOL_MAX_SIZE=50
COMMAND_TIMEOUT=10
```

### Security Checklist

- [ ] Rotate default database credentials
- [ ] Enable SSL/TLS for database connections
- [ ] Add authentication middleware (JWT/OAuth2)
- [ ] Implement rate limiting
- [ ] Run containers as non-root
- [ ] Scan images for CVEs
- [ ] Set up alerting on `db_connection_errors_total`

---

## Tech Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| Framework | FastAPI | 0.95.2 |
| ASGI Server | Uvicorn | 0.23.1 |
| Database Driver | asyncpg | 0.28.0 |
| Database | PostgreSQL | 15 |
| Validation | Pydantic | 1.10.9 |
| Metrics | prometheus-client | 0.17.1 |
| Instrumentation | prometheus-fastapi-instrumentator | 6.1.0 |
| Load Testing | aiohttp | — |
| Container | Docker + Compose | — |
| Dashboards | Grafana | latest |

---

## License

MIT — see [LICENSE](LICENSE).
