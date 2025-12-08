"""Custom Prometheus metrics for database connection pool"""
from prometheus_client import Gauge, Histogram, Counter

# Connection Pool Metrics
db_pool_size = Gauge('db_pool_size', 'Current database connection pool size')
db_pool_max_size = Gauge('db_pool_max_size', 'Maximum database connection pool size')
db_active_connections = Gauge('db_active_connections', 'Number of active database connections')
db_idle_connections = Gauge('db_idle_connections', 'Number of idle database connections')

# Query Performance Metrics
db_query_duration = Histogram(
    'db_query_duration_seconds',
    'Database query execution time',
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0]
)

db_connection_acquire_duration = Histogram(
    'db_connection_acquire_duration_seconds',
    'Time to acquire database connection from pool',
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5]
)

# Error Metrics
db_connection_errors = Counter('db_connection_errors_total', 'Total database connection errors')
db_query_errors = Counter('db_query_errors_total', 'Total database query errors')
