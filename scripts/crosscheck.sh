#!/usr/bin/env bash
set -euo pipefail
free -m
df -h /
uptime -p || true
uptime -s || true
query() { curl -fsS --get --data-urlencode "query=$1" http://127.0.0.1:9090/api/v1/query || echo "Prometheus unavailable"; }
echo "Prometheus RAM:"; query '(1 - node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes) * 100'
echo "Prometheus disk:"; query '100 - (node_filesystem_avail_bytes{mountpoint="/"} / node_filesystem_size_bytes{mountpoint="/"} * 100)'
echo "Prometheus uptime:"; query 'time() - node_boot_time_seconds'
