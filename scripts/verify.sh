#!/usr/bin/env bash
set -euo pipefail
fail=0
check() { if "$@"; then echo "PASS: $1"; else echo "FAIL: $1"; fail=1; fi; }
check docker compose ps
check curl -fsS http://127.0.0.1:8001/health
check sh -c "curl -fsS http://127.0.0.1:8001/metrics | grep -q orders_created_total"
check sh -c "curl -fsS http://127.0.0.1:8001/metrics | grep -q order_request_duration_seconds"
check curl -fsS http://127.0.0.1:9090/-/healthy
check sh -c "curl -fsS http://127.0.0.1:9090/api/v1/targets | grep -q node-exporter"
check sh -c "curl -fsS http://127.0.0.1:9090/api/v1/targets | grep -q order-api"
check curl -fsS http://127.0.0.1:3000/api/health
if curl -fsS http://127.0.0.1:3100/ready >/dev/null; then echo "PASS: loki ready"; else echo "WARN: loki not ready (Kubernetes may not be configured)"; fi
exit "$fail"
